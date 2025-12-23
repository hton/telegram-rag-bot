"""Typing middleware for showing 'typing...' status"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.enums import ChatAction


class TypingMiddleware(BaseMiddleware):
    """Middleware for showing 'typing...' status while processing"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        """Show typing status and call handler"""
        # Send typing action
        await event.bot.send_chat_action(event.chat.id, ChatAction.TYPING)

        return await handler(event, data)
