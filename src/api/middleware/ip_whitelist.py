"""IP Whitelist middleware for API"""
from typing import Callable, Set
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from src.core.config import settings


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware to restrict API access to whitelisted IP addresses

    Config:
        API_ALLOWED_IPS: Comma-separated list of allowed IPs (empty = all allowed)

    Examples:
        API_ALLOWED_IPS=127.0.0.1,192.168.1.100
        API_ALLOWED_IPS=  # Empty = allow all
    """

    # Endpoints that don't require IP whitelist check
    EXEMPT_PATHS = {
        "/health",
    }

    def __init__(self, app):
        super().__init__(app)
        self.allowed_ips: Set[str] = self._parse_allowed_ips()

        if self.allowed_ips:
            logger.info(f"IP Whitelist enabled: {len(self.allowed_ips)} IPs allowed")
            logger.debug(f"Allowed IPs: {', '.join(sorted(self.allowed_ips))}")
        else:
            logger.info("IP Whitelist disabled (all IPs allowed)")

    def _parse_allowed_ips(self) -> Set[str]:
        """Parse comma-separated IP whitelist"""
        if not settings.API_ALLOWED_IPS or not settings.API_ALLOWED_IPS.strip():
            return set()

        try:
            ips = {
                ip.strip()
                for ip in settings.API_ALLOWED_IPS.split(",")
                if ip.strip()
            }
            return ips
        except Exception as e:
            logger.error(f"Error parsing API_ALLOWED_IPS: {e}")
            return set()

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request

        Checks X-Forwarded-For header first (for proxied requests),
        then falls back to direct client IP.
        """
        # Check X-Forwarded-For header (for nginx/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first (original client)
            client_ip = forwarded_for.split(",")[0].strip()
            return client_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable):
        """Check IP whitelist before processing request"""

        # If whitelist is empty, allow all IPs
        if not self.allowed_ips:
            return await call_next(request)

        # Skip whitelist check for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check if IP is in whitelist
        if client_ip not in self.allowed_ips:
            logger.warning(
                f"Access denied for IP {client_ip} to {request.url.path} "
                f"(not in whitelist)"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Access denied",
                    "error": "ip_not_allowed",
                    "message": "Your IP address is not authorized to access this API",
                }
            )

        # IP is whitelisted, process request
        logger.debug(f"Allowed request from whitelisted IP {client_ip}")
        return await call_next(request)
