"""Telegram bot initialization"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from src.core.config import settings
from src.bot.handlers import message, callback, commands
from src.bot.middleware.logging import LoggingMiddleware
from src.bot.middleware.typing import TypingMiddleware
from src.bot.middleware.whitelist import WhitelistMiddleware
from src.bot.middleware.rate_limit import RateLimitMiddleware


def create_bot() -> Bot:
    """Create and configure bot instance"""
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    logger.info("Telegram bot created")
    return bot


def get_dispatcher() -> Dispatcher:
    """Create and configure dispatcher with handlers and middleware"""
    dp = Dispatcher()

    # Register middleware (order matters - security checks first!)
    # 1. Whitelist check (block unauthorized users/groups immediately)
    dp.message.middleware(WhitelistMiddleware())

    # 2. Rate limiting (prevent spam from allowed users)
    dp.message.middleware(RateLimitMiddleware())

    # 3. Logging (log allowed requests)
    dp.message.middleware(LoggingMiddleware())

    # 4. Typing indicator (show bot is working)
    dp.message.middleware(TypingMiddleware())

    # Register routers
    dp.include_router(commands.router)
    dp.include_router(message.router)
    dp.include_router(callback.router)

    logger.info("Dispatcher configured with handlers and middleware")
    return dp
