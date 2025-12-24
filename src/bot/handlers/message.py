"""Message handlers for Telegram bot"""
from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.bot.filters import MentionFilter
from src.bot.keyboards import get_feedback_keyboard
from src.services.query_service import QueryService
from src.services.chat_memory import ChatMemoryService
from src.services.feedback import FeedbackService
from src.rag.pipeline import RAGPipeline
from src.schemas.enums import QuerySource
from src.core.database import AsyncSessionLocal
from src.core.config import settings

router = Router()


def should_request_feedback(answer: str) -> bool:
    """
    Определяет, нужно ли запрашивать оценку ответа.
    Возвращает False если ответ пустой или система не нашла информацию.
    """
    # Ответы, для которых не нужна оценка
    no_feedback_phrases = [
        "Для ответа необходимо уточнить или перефразировать вопрос",
        "База знаний еще не заполнена",
    ]

    return not any(phrase in answer for phrase in no_feedback_phrases)


@router.message(MentionFilter())
async def handle_question(message: types.Message):
    """Handle user questions via Telegram"""
    try:
        # Clean mention from text
        question = message.text.replace(f"@{settings.BOT_USERNAME}", "").strip()

        if not question:
            await message.answer("Пожалуйста, задайте вопрос после упоминания.")
            return

        logger.info(f"Processing question from user {message.from_user.id}: {question[:100]}...")

        # Create database session
        async with AsyncSessionLocal() as db:
            # Initialize services
            rag_pipeline = RAGPipeline(db)
            memory_service = ChatMemoryService(db)
            feedback_service = FeedbackService(db)
            query_service = QueryService(db, rag_pipeline, memory_service, feedback_service)

            # Process query through unified service
            result = await query_service.process_query(
                question=question,
                user_id=str(message.from_user.id),
                source=QuerySource.TELEGRAM,
                enable_memory=True,
                enable_feedback=settings.TELEGRAM_ENABLE_FEEDBACK,
                metadata={
                    "chat_id": message.chat.id,
                    "message_id": message.message_id,
                    "username": message.from_user.username,
                    "first_name": message.from_user.first_name,
                },
            )

            # Send answer
            await message.answer(
                result.answer,
                parse_mode="Markdown",
            )

            # Send feedback buttons if enabled and answer is valid
            if settings.TELEGRAM_ENABLE_FEEDBACK and should_request_feedback(result.answer):
                await message.answer(
                    "Оцените качество ответа:",
                    reply_markup=get_feedback_keyboard(result.query_id),
                )

            logger.info(
                f"Answer sent to user {message.from_user.id}, "
                f"processing time: {result.processing_time_ms:.2f}ms"
            )

    except Exception as e:
        logger.error("Error handling question: {}", e, exc_info=True)
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )
