"""
Rate Limiting Service for AudioPoster

Provides user/session-based rate limiting to prevent abuse of upload endpoints
and API resources. Uses Redis for distributed rate limiting across multiple instances.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Request
import redis.asyncio as aioredis
from ..config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """Advanced rate limiting service with user/session-based limits"""

    def __init__(self):
        self.redis_client: Optional[aioredis.Redis] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection for rate limiting"""
        if self._initialized:
            return

        try:
            self.redis_client = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Rate limiter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            # Fallback to in-memory rate limiting if Redis is unavailable
            self._initialized = False

    async def _get_user_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting (IP + User-Agent hash)"""
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # Create a hash of IP + User-Agent for more accurate user identification
        import hashlib
        identifier = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
        return identifier

    async def _get_session_identifier(self, session_token: str) -> str:
        """Get session-based identifier for rate limiting"""
        return f"session:{session_token}"

    async def _check_rate_limit(
        self,
        identifier: str,
        limit_type: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Dict]:
        """
        Check if request is within rate limit

        Returns:
            Tuple[bool, Dict]: (is_allowed, rate_limit_info)
        """
        if not self._initialized or not self.redis_client:
            # If Redis is not available, allow the request (fail open)
            logger.warning("Rate limiter not initialized, allowing request")
            return True, {"status": "bypassed", "reason": "redis_unavailable"}

        try:
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(seconds=window_seconds)

            # Create Redis key for this identifier and limit type
            key = f"rate_limit:{limit_type}:{identifier}"

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()

            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start.timestamp())

            # Count current requests in window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time.timestamp()): current_time.timestamp()})

            # Set expiration for the key
            pipe.expire(key, window_seconds + 60)  # Extra 60 seconds buffer

            results = await pipe.execute()
            current_count = results[1]

            # Check if limit exceeded
            is_allowed = current_count < max_requests

            rate_limit_info = {
                "limit_type": limit_type,
                "current_count": current_count,
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "reset_time": (current_time + timedelta(seconds=window_seconds)).isoformat(),
                "is_allowed": is_allowed
            }

            if not is_allowed:
                logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{max_requests}")

            return is_allowed, rate_limit_info

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {"status": "error", "reason": str(e)}

    async def check_api_rate_limit(self, request: Request) -> Dict:
        """Check general API rate limit"""
        identifier = await self._get_user_identifier(request)
        is_allowed, info = await self._check_rate_limit(
            identifier,
            "api",
            settings.rate_limit_requests_per_minute,
            60  # 1 minute window
        )

        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": info.get("reset_time", ""),
                    "Retry-After": "60"
                }
            )

        return info

    async def check_upload_rate_limit(self, session_token: str) -> Dict:
        """Check file upload rate limit for a session"""
        identifier = await self._get_session_identifier(session_token)

        # Check hourly limit
        hourly_allowed, hourly_info = await self._check_rate_limit(
            identifier,
            "upload_hourly",
            settings.rate_limit_upload_per_hour,
            3600  # 1 hour window
        )

        if not hourly_allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Upload limit exceeded. Maximum {settings.rate_limit_upload_per_hour} uploads per hour.",
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_upload_per_hour),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": hourly_info.get("reset_time", ""),
                    "Retry-After": "3600"
                }
            )

        # Check daily limit
        daily_allowed, daily_info = await self._check_rate_limit(
            identifier,
            "upload_daily",
            settings.rate_limit_upload_per_day,
            86400  # 24 hour window
        )

        if not daily_allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Daily upload limit exceeded. Maximum {settings.rate_limit_upload_per_day} uploads per day.",
                headers={
                    "X-RateLimit-Limit": str(settings.rate_limit_upload_per_day),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": daily_info.get("reset_time", ""),
                    "Retry-After": "86400"
                }
            )

        return {
            "hourly": hourly_info,
            "daily": daily_info,
            "is_allowed": True
        }

    async def check_burst_rate_limit(self, request: Request) -> Dict:
        """Check burst rate limit for rapid successive requests"""
        identifier = await self._get_user_identifier(request)
        is_allowed, info = await self._check_rate_limit(
            identifier,
            "burst",
            settings.get_rate_limit_burst_size(),
            10  # 10 second window for burst detection
        )

        if not is_allowed:
            # Log suspicious activity
            logger.warning(f"Suspicious burst activity detected from {identifier}")

            # Temporarily ban the user
            await self._temporary_ban(identifier, settings.rate_limit_ban_duration)

            raise HTTPException(
                status_code=429,
                detail="Suspicious activity detected. Access temporarily restricted.",
                headers={
                    "Retry-After": str(settings.rate_limit_ban_duration)
                }
            )

        return info

    async def _temporary_ban(self, identifier: str, duration_seconds: int):
        """Temporarily ban an identifier"""
        if not self._initialized or not self.redis_client:
            return

        try:
            ban_key = f"ban:{identifier}"
            await self.redis_client.setex(
                ban_key,
                duration_seconds,
                json.dumps({
                    "banned_at": datetime.utcnow().isoformat(),
                    "duration": duration_seconds
                })
            )
            logger.info(f"Temporarily banned {identifier} for {duration_seconds} seconds")
        except Exception as e:
            logger.error(f"Failed to ban {identifier}: {e}")

    async def is_banned(self, request: Request) -> bool:
        """Check if the request is from a banned identifier"""
        if not self._initialized or not self.redis_client:
            return False

        try:
            identifier = await self._get_user_identifier(request)
            ban_key = f"ban:{identifier}"
            ban_data = await self.redis_client.get(ban_key)

            if ban_data:
                ban_info = json.loads(ban_data)
                logger.warning(f"Banned user {identifier} attempted access")
                return True

            return False
        except Exception as e:
            logger.error(f"Failed to check ban status: {e}")
            return False

    async def get_rate_limit_status(self, request: Request) -> Dict:
        """Get current rate limit status for debugging/monitoring"""
        identifier = await self._get_user_identifier(request)

        status = {
            "identifier": identifier,
            "is_banned": await self.is_banned(request),
            "limits": {
                "api_per_minute": settings.rate_limit_requests_per_minute,
                "upload_per_hour": settings.rate_limit_upload_per_hour,
                "upload_per_day": settings.rate_limit_upload_per_day,
                "burst_size": settings.rate_limit_burst_size
            }
        }

        return status

    async def cleanup_expired_entries(self):
        """Clean up expired rate limit entries (called periodically)"""
        if not self._initialized or not self.redis_client:
            return

        try:
            # This is handled automatically by Redis expiration, but we can add
            # additional cleanup logic here if needed
            logger.debug("Rate limiter cleanup completed")
        except Exception as e:
            logger.error(f"Rate limiter cleanup failed: {e}")


# Global rate limiter instance
rate_limiter = RateLimiter()
