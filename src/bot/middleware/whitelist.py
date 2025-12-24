"""Whitelist middleware to restrict bot access"""
from typing import Callable, Dict, Any, Awaitable, Set
from aiogram import BaseMiddleware
from aiogram.types import Message
from loguru import logger

from src.core.config import settings


class WhitelistMiddleware(BaseMiddleware):
    """
    Whitelist middleware to control bot access

    Features:
    - User whitelist for private chats
    - Group/chat whitelist for group chats

    Config:
        WHITELIST_USERS_ENABLED: Enable user whitelist
        WHITELIST_USERS: Comma-separated user IDs
        WHITELIST_GROUPS_ENABLED: Enable group whitelist
        WHITELIST_GROUPS: Comma-separated group/chat IDs
    """

    def __init__(self):
        super().__init__()
        self.allowed_users: Set[int] = self._parse_whitelist(settings.WHITELIST_USERS)
        self.allowed_groups: Set[int] = self._parse_whitelist(settings.WHITELIST_GROUPS)

        if settings.WHITELIST_USERS_ENABLED:
            logger.info(f"User whitelist enabled: {len(self.allowed_users)} users")
        if settings.WHITELIST_GROUPS_ENABLED:
            logger.info(f"Group whitelist enabled: {len(self.allowed_groups)} groups")

    def _parse_whitelist(self, whitelist_str: str) -> Set[int]:
        """Parse comma-separated whitelist string to set of integers"""
        if not whitelist_str or not whitelist_str.strip():
            return set()

        try:
            return {
                int(item.strip())
                for item in whitelist_str.split(",")
                if item.strip()
            }
        except ValueError as e:
            logger.error(f"Error parsing whitelist: {e}")
            return set()

    def _is_private_chat(self, message: Message) -> bool:
        """Check if message is from private chat"""
        return message.chat.type == "private"

    def _is_group_chat(self, message: Message) -> bool:
        """Check if message is from group/supergroup"""
        return message.chat.type in ("group", "supergroup")

    def _check_user_access(self, user_id: int) -> tuple[bool, str]:
        """
        Check if user is allowed to use bot in private chat

        Returns:
            (allowed, error_message)
        """
        if not settings.WHITELIST_USERS_ENABLED:
            return True, ""

        # If whitelist is empty, allow all
        if not self.allowed_users:
            return True, ""

        # Check if user in whitelist
        if user_id in self.allowed_users:
            return True, ""

        logger.warning(f"Access denied for user {user_id} (not in whitelist)")
        return False, (
            "🔒 Извините, доступ к боту ограничен.\n"
            "Для получения доступа обратитесь к администратору."
        )

    def _check_group_access(self, chat_id: int, user_id: int) -> tuple[bool, str]:
        """
        Check if group is allowed

        Returns:
            (allowed, error_message)
        """
        if not settings.WHITELIST_GROUPS_ENABLED:
            return True, ""

        # If whitelist is empty, allow all
        if not self.allowed_groups:
            return True, ""

        # Check if group in whitelist
        if chat_id in self.allowed_groups:
            return True, ""

        logger.warning(
            f"Access denied for user {user_id} in group {chat_id} "
            f"(group not in whitelist)"
        )
        return False, (
            "🔒 Бот не активирован в этой группе.\n"
            "Для активации обратитесь к администратору."
        )

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Check whitelist before processing message"""

        # Skip if not a message or no user
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        chat_id = event.chat.id

        # Check access based on chat type
        if self._is_private_chat(event):
            # Private chat - check user whitelist
            allowed, error_message = self._check_user_access(user_id)

            if not allowed:
                await event.answer(error_message)
                logger.info(f"Whitelist blocked user {user_id} in private chat")
                return  # Don't process the message

        elif self._is_group_chat(event):
            # Group chat - check group whitelist
            allowed, error_message = self._check_group_access(chat_id, user_id)

            if not allowed:
                await event.answer(error_message)
                logger.info(f"Whitelist blocked user {user_id} in group {chat_id}")
                return  # Don't process the message

        # Access granted, process message normally
        return await handler(event, data)
