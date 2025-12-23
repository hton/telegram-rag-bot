"""Custom filters for Telegram bot"""
from typing import Union
from aiogram.filters import BaseFilter
from aiogram.types import Message
from loguru import logger

from src.core.config import settings


class MentionFilter(BaseFilter):
    """Filter messages that mention the bot"""

    async def __call__(self, message: Message) -> bool:
        """Check if message mentions the bot"""
        if not message.text:
            return False

        # Check if message has entities
        if not message.entities:
            return False

        # Check if first entity is a mention
        first_entity = message.entities[0]
        if first_entity.type != "mention":
            return False

        # Check if mention is the bot's username
        mention = message.text[first_entity.offset:first_entity.offset + first_entity.length]
        is_bot_mention = mention == f"@{settings.BOT_USERNAME}"

        logger.debug(f"Mention filter: {mention} == @{settings.BOT_USERNAME} = {is_bot_mention}")

        return is_bot_mention
