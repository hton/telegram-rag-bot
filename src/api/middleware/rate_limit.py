"""Rate limiting middleware for API"""
from typing import Callable, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from src.core.config import settings


class APIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for API endpoints

    Tracks requests per IP address and enforces limits:
    - Requests per minute
    - Requests per hour

    Config:
        API_RATE_LIMIT_ENABLED: Enable/disable rate limiting
        API_RATE_LIMIT_REQUESTS_PER_MINUTE: Max requests per minute per IP
        API_RATE_LIMIT_REQUESTS_PER_HOUR: Max requests per hour per IP
    """

    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {
        "/health",
    }

    def __init__(self, app):
        super().__init__(app)
        self.ip_requests: Dict[str, list] = defaultdict(list)

        if settings.API_RATE_LIMIT_ENABLED:
            logger.info(
                f"API Rate limiting enabled: "
                f"{settings.API_RATE_LIMIT_REQUESTS_PER_MINUTE}/min, "
                f"{settings.API_RATE_LIMIT_REQUESTS_PER_HOUR}/hour"
            )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address (same logic as IPWhitelistMiddleware)"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _clean_old_requests(self, ip: str, now: datetime):
        """Remove requests older than 1 hour"""
        if ip in self.ip_requests:
            self.ip_requests[ip] = [
                req_time for req_time in self.ip_requests[ip]
                if now - req_time < timedelta(hours=1)
            ]

    def _check_rate_limit(self, ip: str) -> tuple[bool, str, int]:
        """
        Check if IP exceeded rate limits

        Returns:
            (allowed, error_message, retry_after_seconds)
        """
        if not settings.API_RATE_LIMIT_ENABLED:
            return True, "", 0

        now = datetime.now()

        # Clean old requests
        self._clean_old_requests(ip, now)

        # Get IP's recent requests
        ip_reqs = self.ip_requests[ip]

        # Check requests per minute
        requests_last_minute = sum(
            1 for req_time in ip_reqs
            if now - req_time < timedelta(minutes=1)
        )

        if requests_last_minute >= settings.API_RATE_LIMIT_REQUESTS_PER_MINUTE:
            logger.warning(
                f"API Rate limit (per minute) exceeded for IP {ip}: "
                f"{requests_last_minute}/{settings.API_RATE_LIMIT_REQUESTS_PER_MINUTE}"
            )
            return False, (
                f"Rate limit exceeded. "
                f"Maximum {settings.API_RATE_LIMIT_REQUESTS_PER_MINUTE} requests per minute allowed."
            ), 60

        # Check requests per hour
        requests_last_hour = len(ip_reqs)

        if requests_last_hour >= settings.API_RATE_LIMIT_REQUESTS_PER_HOUR:
            logger.warning(
                f"API Rate limit (per hour) exceeded for IP {ip}: "
                f"{requests_last_hour}/{settings.API_RATE_LIMIT_REQUESTS_PER_HOUR}"
            )
            return False, (
                f"Hourly rate limit exceeded. "
                f"Maximum {settings.API_RATE_LIMIT_REQUESTS_PER_HOUR} requests per hour allowed."
            ), 3600

        # Record this request
        self.ip_requests[ip].append(now)

        # Log usage stats
        logger.debug(
            f"API IP {ip} rate limit: {requests_last_minute}/min, "
            f"{requests_last_hour}/hour"
        )

        return True, "", 0

    async def dispatch(self, request: Request, call_next: Callable):
        """Check rate limits before processing request"""

        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check rate limit
        allowed, error_message, retry_after = self._check_rate_limit(client_ip)

        if not allowed:
            return JSONResponse(
                status_code=429,  # Too Many Requests
                content={
                    "detail": error_message,
                    "error": "rate_limit_exceeded",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                }
            )

        # Process request normally
        return await call_next(request)
