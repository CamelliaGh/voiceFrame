"""
Security Headers Middleware

This middleware adds security headers to all HTTP responses
to protect against common web vulnerabilities.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""

    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment

        # Security headers configuration
        self.security_headers = {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Permissions policy (formerly Feature Policy)
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=(), "
                "accelerometer=(), ambient-light-sensor=(), autoplay=(), "
                "battery=(), display-capture=(), document-domain=(), "
                "encrypted-media=(), execution-while-not-rendered=(), "
                "execution-while-out-of-viewport=(), fullscreen=(), "
                "gamepad=(), layout-animations=(), legacy-image-formats=(), "
                "magnetometer=(), midi=(), oversized-images=(), "
                "picture-in-picture=(), publickey-credentials-get=(), "
                "sync-xhr=(), unoptimized-images=(), unsized-media=(), "
                "usb=(), wake-lock=(), xr-spatial-tracking=()"
            ),

            # Cross-Origin policies
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

        # Add stricter headers for production
        if environment == "production":
            self.security_headers.update({
                # Force HTTPS in production
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",

                # Content Security Policy (CSP)
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://static.cloudflareinsights.com; "
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com; "
                    "img-src 'self' data: https: blob:; "
                    "media-src 'self' https://*.s3.amazonaws.com https://*.s3.us-east-2.amazonaws.com; "
                    "connect-src 'self' https://api.stripe.com https://api.sendgrid.com https://cloudflareinsights.com; "
                    "frame-src https://js.stripe.com; "
                    "object-src 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'; "
                    "frame-ancestors 'none'; "
                    "upgrade-insecure-requests"
                ),

                # Remove server information
                "Server": "AudioPoster",
            })
        else:
            # More permissive CSP for development
            self.security_headers.update({
                "Content-Security-Policy": (
                    "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
                    "connect-src 'self' http://localhost:* https://api.stripe.com https://cloudflareinsights.com; "
                    "img-src 'self' data: https: blob:; "
                    "media-src 'self' https://*.s3.amazonaws.com https://*.s3.us-east-2.amazonaws.com; "
                    "font-src 'self' data:; "
                    "object-src 'none'; "
                    "base-uri 'self'"
                ),
            })

    async def dispatch(self, request: Request, call_next):
        """Add security headers to the response"""
        response = await call_next(request)

        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value

        # Log security events for monitoring
        if self._is_suspicious_request(request):
            logger.warning(f"Suspicious request detected: {request.client.host} - {request.url}")

        return response

    def _is_suspicious_request(self, request: Request) -> bool:
        """Detect potentially suspicious requests"""
        suspicious_indicators = [
            # Common attack patterns in URL
            "..",  # Path traversal
            "<script",  # XSS attempts
            "javascript:",  # JavaScript injection
            "data:text/html",  # Data URI attacks
            "eval(",  # Code injection
            "exec(",  # Command injection
            "union select",  # SQL injection
            "drop table",  # SQL injection
            "admin",  # Admin panel access attempts
            "wp-admin",  # WordPress attacks
            "phpmyadmin",  # Database admin access
            ".env",  # Environment file access
            "config",  # Configuration access
        ]

        url_str = str(request.url).lower()
        user_agent = request.headers.get("user-agent", "").lower()

        # Check for suspicious patterns in URL
        for indicator in suspicious_indicators:
            if indicator in url_str:
                return True

        # Check for suspicious user agents
        suspicious_user_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burp",
            "wget", "curl", "python-requests", "bot", "crawler",
            "scanner", "exploit", "hack"
        ]

        for agent in suspicious_user_agents:
            if agent in user_agent:
                return True

        return False

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse"""

    def __init__(self, app, requests_per_minute: int = 60, burst_size: int = 5):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.request_counts = {}

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting"""
        # Import here to avoid circular imports
        from ..config import settings

        # Skip rate limiting in development environment
        if not settings.is_rate_limit_enabled():
            return await call_next(request)

        client_ip = request.client.host
        current_time = int(request.scope.get("time", 0))
        minute_window = current_time // 60

        # Clean old entries
        self._cleanup_old_entries(minute_window)

        # Check rate limit
        key = f"{client_ip}:{minute_window}"
        current_count = self.request_counts.get(key, 0)

        if current_count >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={"Retry-After": "60"}
            )

        # Increment counter
        self.request_counts[key] = current_count + 1

        response = await call_next(request)
        return response

    def _cleanup_old_entries(self, current_minute: int):
        """Remove old rate limit entries"""
        keys_to_remove = []
        for key in self.request_counts:
            try:
                ip, minute = key.split(":")
                if int(minute) < current_minute - 1:  # Keep current and previous minute
                    keys_to_remove.append(key)
            except (ValueError, IndexError):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.request_counts[key]

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log security-relevant events"""

    async def dispatch(self, request: Request, call_next):
        """Log security events"""
        start_time = request.scope.get("time", 0)

        response = await call_next(request)

        # Log security events
        if response.status_code >= 400:
            logger.warning(
                f"HTTP {response.status_code} for {request.method} {request.url.path} "
                f"from {request.client.host} - User-Agent: {request.headers.get('user-agent', 'Unknown')}"
            )

        # Log potential security issues
        if response.status_code in [401, 403, 429]:
            logger.warning(
                f"Security event: {response.status_code} for {request.method} {request.url.path} "
                f"from {request.client.host}"
            )

        return response
