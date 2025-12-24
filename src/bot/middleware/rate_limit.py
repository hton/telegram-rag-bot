"""Rate limiting middleware to prevent spam and abuse"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.config import settings


class RateLimitMiddleware(BaseMiddleware):
    """
    Rate limiting middleware to prevent spam and excessive API usage

    Tracks requests per user and enforces limits:
    - Requests per minute
    - Requests per hour

    Config:
        RATE_LIMIT_ENABLED: Enable/disable rate limiting
        RATE_LIMIT_REQUESTS_PER_MINUTE: Max requests per minute
        RATE_LIMIT_REQUESTS_PER_HOUR: Max requests per hour
    """

    def __init__(self):
        super().__init__()
        self.user_requests: Dict[int, list] = defaultdict(list)

    def _clean_old_requests(self, user_id: int, now: datetime):
        """Remove requests older than 1 hour"""
        if user_id in self.user_requests:
            # Keep only requests from last hour
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if now - req_time < timedelta(hours=1)
            ]

    def _check_rate_limit(self, user_id: int) -> tuple[bool, str]:
        """
        Check if user exceeded rate limits

        Returns:
            (allowed, message) - True if allowed, False if rate limited
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, ""

        now = datetime.now()

        # Clean old requests
        self._clean_old_requests(user_id, now)

        # Get user's recent requests
        user_reqs = self.user_requests[user_id]

        # Check requests per minute
        requests_last_minute = sum(
            1 for req_time in user_reqs
            if now - req_time < timedelta(minutes=1)
        )

        if requests_last_minute >= settings.RATE_LIMIT_REQUESTS_PER_MINUTE:
            logger.warning(
                f"Rate limit (per minute) exceeded for user {user_id}: "
                f"{requests_last_minute}/{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}"
            )
            return False, (
                f"⏱ Превышен лимит запросов.\n"
                f"Максимум {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} запросов в минуту.\n"
                f"Пожалуйста, подождите немного."
            )

        # Check requests per hour
        requests_last_hour = len(user_reqs)

        if requests_last_hour >= settings.RATE_LIMIT_REQUESTS_PER_HOUR:
            logger.warning(
                f"Rate limit (per hour) exceeded for user {user_id}: "
                f"{requests_last_hour}/{settings.RATE_LIMIT_REQUESTS_PER_HOUR}"
            )
            return False, (
                f"⏱ Превышен часовой лимит запросов.\n"
                f"Максимум {settings.RATE_LIMIT_REQUESTS_PER_HOUR} запросов в час.\n"
                f"Попробуйте позже."
            )

        # Record this request
        self.user_requests[user_id].append(now)

        # Log usage stats
        logger.debug(
            f"User {user_id} rate limit: {requests_last_minute}/min, "
            f"{requests_last_hour}/hour"
        )

        return True, ""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Check rate limits before processing message"""

        # Skip if not a message or no user
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id

        # Check rate limit
        allowed, error_message = self._check_rate_limit(user_id)

        if not allowed:
            # Send rate limit message to user
            await event.answer(error_message)
            logger.info(f"Rate limit blocked user {user_id}")
            return  # Don't process the message

        # Process message normally
        return await handler(event, data)
