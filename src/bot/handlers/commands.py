"""Command handlers for Telegram bot"""
from aiogram import Router, types
from aiogram.filters import Command
from loguru import logger

from src.core.config import settings

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command"""
    welcome_text = """
Привет! 👋

Я IT-помощник, готовый ответить на ваши вопросы.

**Как пользоваться:**
Просто упомяните меня в сообщении (@{}) и задайте вопрос.

Например:
`@{} Как установить платформу?`

**Команды:**
/help - показать это сообщение
/start - начать работу
    """.format(settings.BOT_USERNAME, settings.BOT_USERNAME)

    await message.answer(welcome_text)
    logger.info(f"User {message.from_user.id} started the bot")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command"""
    help_text = """
**Справка**

Я отвечаю на вопросы по IT-тематике на основе документации.

**Как задать вопрос:**
Упомяните меня (@{}) в сообщении и напишите вопрос.

**Примеры:**
• @{} Что такое ЕКП?
• @{} Как установить платформу в закрытом контуре?
• @{} Какие требования к серверу?

**Оценка ответов:**
После получения ответа вы можете оценить его качество с помощью кнопок 👍👌👎

**Команды:**
/start - начать работу
/help - показать эту справку
    """.format(settings.BOT_USERNAME, settings.BOT_USERNAME, settings.BOT_USERNAME)

    await message.answer(help_text)
    logger.info(f"User {message.from_user.id} requested help")
