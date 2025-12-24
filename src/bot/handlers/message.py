"""Message handlers for Telegram bot"""
from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import time

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
    """Handle user questions via Telegram with streaming"""
    try:
        # Clean mention from text
        question = message.text.replace(f"@{settings.BOT_USERNAME}", "").strip()

        if not question:
            await message.answer("Пожалуйста, задайте вопрос после упоминания.")
            return

        logger.info(f"Processing question from user {message.from_user.id}: {question[:100]}...")

        # Send "typing" indicator
        await message.bot.send_chat_action(message.chat.id, "typing")

        # Create database session
        async with AsyncSessionLocal() as db:
            # Initialize services
            rag_pipeline = RAGPipeline(db)
            memory_service = ChatMemoryService(db)
            feedback_service = FeedbackService(db)
            query_service = QueryService(
                db=db,
                rag_pipeline=rag_pipeline,
                memory_service=memory_service,
                feedback_service=feedback_service,
            )

            # Process query with streaming using QueryService
            current_text = ""
            sent_message = None
            last_update = time.time()
            update_interval = 1.0  # Update every 1 second
            query_id = None

            async for chunk_tuple in query_service.process_query_stream(
                question=question,
                user_id=str(message.from_user.id),
                source=QuerySource.TELEGRAM,
                enable_memory=True,
                enable_feedback=settings.TELEGRAM_ENABLE_FEEDBACK,
            ):
                qid, chunk = chunk_tuple

                # First yield contains query_id
                if query_id is None:
                    query_id = qid
                    continue

                # Accumulate chunks
                current_text += chunk

                # Update message every second or when we have enough new content
                if time.time() - last_update > update_interval and len(current_text) > 50:
                    try:
                        if sent_message is None:
                            # Send first message
                            sent_message = await message.answer(
                                current_text + "...",
                                parse_mode="Markdown",
                            )
                        else:
                            # Edit existing message
                            await sent_message.edit_text(
                                current_text + "...",
                                parse_mode="Markdown",
                            )
                        last_update = time.time()
                    except Exception as e:
                        # Ignore edit errors (message didn't change, etc.)
                        pass

            # Final update with complete answer
            if sent_message:
                try:
                    await sent_message.edit_text(current_text, parse_mode="Markdown")
                except Exception:
                    pass
            else:
                sent_message = await message.answer(current_text, parse_mode="Markdown")

            # Send feedback buttons if enabled and answer is valid
            if settings.TELEGRAM_ENABLE_FEEDBACK and should_request_feedback(current_text) and query_id:
                await message.answer(
                    "Оцените качество ответа:",
                    reply_markup=get_feedback_keyboard(query_id),
                )

            logger.info(f"Answer sent to user {message.from_user.id}, query_id: {query_id}")

    except Exception as e:
        logger.error("Error handling question: {}", e, exc_info=True)
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )
