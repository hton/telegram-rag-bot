"""API Key authentication middleware"""
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from src.core.config import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication

    Checks X-API-Key header against configured API_KEY.
    Exempts health check endpoints from authentication.

    Config:
        API_REQUIRE_AUTH: Enable/disable API key authentication
        API_KEY: The secret API key
    """

    # Endpoints that don't require authentication
    EXEMPT_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    def __init__(self, app):
        super().__init__(app)
        self.enabled = settings.API_REQUIRE_AUTH
        self.api_key = settings.API_KEY

        if self.enabled:
            if not self.api_key:
                logger.warning(
                    "API_REQUIRE_AUTH is enabled but API_KEY is not set! "
                    "API will be accessible without authentication."
                )
                self.enabled = False
            else:
                logger.info("API Key authentication enabled")

    async def dispatch(self, request: Request, call_next: Callable):
        """Check API key before processing request"""

        # Skip if authentication is disabled
        if not self.enabled:
            return await call_next(request)

        # Skip authentication for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip authentication for metrics endpoint
        if request.url.path.startswith("/metrics"):
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        # Check if API key is valid
        if not api_key or api_key != self.api_key:
            logger.warning(
                f"Unauthorized API access attempt from {request.client.host} "
                f"to {request.url.path}"
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid or missing API key",
                    "error": "unauthorized",
                    "hint": "Provide a valid API key in X-API-Key header"
                }
            )

        # API key is valid, process request
        return await call_next(request)
