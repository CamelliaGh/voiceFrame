"""
Tests for Rate Limiting Service

Tests the rate limiting functionality including user-based limits,
burst detection, and temporary banning.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.testclient import TestClient

from ..services.rate_limiter import RateLimiter
from ..main import app


class TestRateLimiter:
    """Test cases for RateLimiter service"""

    @pytest.fixture
    def rate_limiter(self):
        """Create a rate limiter instance for testing"""
        return RateLimiter()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request object"""
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}
        return request

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.ping.return_value = True
        redis_mock.pipeline.return_value.__aenter__.return_value = AsyncMock()
        return redis_mock

    @pytest.mark.asyncio
    async def test_initialization_success(self, rate_limiter, mock_redis):
        """Test successful rate limiter initialization"""
        with patch('aioredis.from_url', return_value=mock_redis):
            await rate_limiter.initialize()
            assert rate_limiter._initialized is True
            assert rate_limiter.redis_client == mock_redis

    @pytest.mark.asyncio
    async def test_initialization_failure(self, rate_limiter):
        """Test rate limiter initialization failure"""
        with patch('aioredis.from_url', side_effect=Exception("Connection failed")):
            await rate_limiter.initialize()
            assert rate_limiter._initialized is False
            assert rate_limiter.redis_client is None

    @pytest.mark.asyncio
    async def test_get_user_identifier(self, rate_limiter, mock_request):
        """Test user identifier generation"""
        identifier = await rate_limiter._get_user_identifier(mock_request)
        assert identifier.startswith("127.0.0.1:")
        assert len(identifier) > 10  # Should include hash

    @pytest.mark.asyncio
    async def test_get_session_identifier(self, rate_limiter):
        """Test session identifier generation"""
        session_token = "test-session-123"
        identifier = await rate_limiter._get_session_identifier(session_token)
        assert identifier == "session:test-session-123"

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limiter, mock_redis):
        """Test rate limit check when request is allowed"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 2, None, None]  # current_count = 2
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        is_allowed, info = await rate_limiter._check_rate_limit(
            "test-identifier", "test-type", 5, 60
        )

        assert is_allowed is True
        assert info["current_count"] == 2
        assert info["max_requests"] == 5
        assert info["is_allowed"] is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, rate_limiter, mock_redis):
        """Test rate limit check when limit is exceeded"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results - current count exceeds limit
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 6, None, None]  # current_count = 6
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        is_allowed, info = await rate_limiter._check_rate_limit(
            "test-identifier", "test-type", 5, 60
        )

        assert is_allowed is False
        assert info["current_count"] == 6
        assert info["max_requests"] == 5
        assert info["is_allowed"] is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_unavailable(self, rate_limiter):
        """Test rate limit check when Redis is unavailable"""
        rate_limiter._initialized = False

        is_allowed, info = await rate_limiter._check_rate_limit(
            "test-identifier", "test-type", 5, 60
        )

        assert is_allowed is True  # Should fail open
        assert info["status"] == "bypassed"
        assert info["reason"] == "redis_unavailable"

    @pytest.mark.asyncio
    async def test_check_api_rate_limit_success(self, rate_limiter, mock_request, mock_redis):
        """Test successful API rate limit check"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 3, None, None]  # current_count = 3
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        info = await rate_limiter.check_api_rate_limit(mock_request)
        assert info["is_allowed"] is True

    @pytest.mark.asyncio
    async def test_check_api_rate_limit_exceeded(self, rate_limiter, mock_request, mock_redis):
        """Test API rate limit check when limit is exceeded"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results - current count exceeds limit
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 15, None, None]  # current_count = 15
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        with pytest.raises(Exception) as exc_info:
            await rate_limiter.check_api_rate_limit(mock_request)

        assert "Too many requests" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_upload_rate_limit_success(self, rate_limiter, mock_redis):
        """Test successful upload rate limit check"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results for both hourly and daily checks
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 5, None, None]  # current_count = 5
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        info = await rate_limiter.check_upload_rate_limit("test-session")
        assert info["is_allowed"] is True
        assert "hourly" in info
        assert "daily" in info

    @pytest.mark.asyncio
    async def test_check_upload_rate_limit_hourly_exceeded(self, rate_limiter, mock_redis):
        """Test upload rate limit check when hourly limit is exceeded"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results - hourly limit exceeded
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 25, None, None]  # current_count = 25
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        with pytest.raises(Exception) as exc_info:
            await rate_limiter.check_upload_rate_limit("test-session")

        assert "Upload limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_burst_rate_limit_success(self, rate_limiter, mock_request, mock_redis):
        """Test successful burst rate limit check"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 2, None, None]  # current_count = 2
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        info = await rate_limiter.check_burst_rate_limit(mock_request)
        assert info["is_allowed"] is True

    @pytest.mark.asyncio
    async def test_check_burst_rate_limit_exceeded(self, rate_limiter, mock_request, mock_redis):
        """Test burst rate limit check when limit is exceeded"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis pipeline results - burst limit exceeded
        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = [None, 8, None, None]  # current_count = 8
        mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipeline

        with pytest.raises(Exception) as exc_info:
            await rate_limiter.check_burst_rate_limit(mock_request)

        assert "Suspicious activity detected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_temporary_ban(self, rate_limiter, mock_redis):
        """Test temporary banning functionality"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        await rate_limiter._temporary_ban("test-identifier", 3600)

        # Verify Redis setex was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "ban:test-identifier"
        assert call_args[0][1] == 3600

    @pytest.mark.asyncio
    async def test_is_banned_true(self, rate_limiter, mock_request, mock_redis):
        """Test ban check when user is banned"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis to return ban data
        ban_data = '{"banned_at": "2023-01-01T00:00:00", "duration": 3600}'
        mock_redis.get.return_value = ban_data

        is_banned = await rate_limiter.is_banned(mock_request)
        assert is_banned is True

    @pytest.mark.asyncio
    async def test_is_banned_false(self, rate_limiter, mock_request, mock_redis):
        """Test ban check when user is not banned"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis to return None (no ban data)
        mock_redis.get.return_value = None

        is_banned = await rate_limiter.is_banned(mock_request)
        assert is_banned is False

    @pytest.mark.asyncio
    async def test_get_rate_limit_status(self, rate_limiter, mock_request, mock_redis):
        """Test getting rate limit status"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        # Mock Redis to return None (not banned)
        mock_redis.get.return_value = None

        status = await rate_limiter.get_rate_limit_status(mock_request)

        assert "identifier" in status
        assert "is_banned" in status
        assert "limits" in status
        assert status["is_banned"] is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_entries(self, rate_limiter, mock_redis):
        """Test cleanup of expired rate limit entries"""
        rate_limiter.redis_client = mock_redis
        rate_limiter._initialized = True

        await rate_limiter.cleanup_expired_entries()

        # Should complete without errors
        assert True


class TestRateLimitingIntegration:
    """Integration tests for rate limiting with FastAPI"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_rate_limit_status_endpoint(self, client):
        """Test rate limit status endpoint"""
        response = client.get("/api/security/rate-limit-status")
        assert response.status_code == 200
        data = response.json()
        assert "identifier" in data
        assert "limits" in data

    def test_content_filter_status_endpoint(self, client):
        """Test content filter status endpoint"""
        response = client.get("/api/security/content-filter-status")
        assert response.status_code == 200
        data = response.json()
        assert "content_filter_enabled" in data
        assert "virus_scan_enabled" in data

    def test_cleanup_rate_limits_endpoint(self, client):
        """Test cleanup rate limits endpoint"""
        response = client.post("/api/security/cleanup-rate-limits")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
