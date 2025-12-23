"""Logging middleware for Telegram bot"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging incoming messages"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        """Log incoming message and call handler"""
        logger.info(
            f"Message from user {event.from_user.id} (@{event.from_user.username}): "
            f"{event.text[:100] if event.text else '[no text]'}..."
        )

        return await handler(event, data)
