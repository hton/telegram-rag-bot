"""Message handlers for Telegram bot"""
import asyncio
from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.bot.filters import MentionFilter
from src.bot.keyboards import get_feedback_keyboard
from src.bot.utils import split_message, fix_html, TELEGRAM_MAX_MESSAGE_LENGTH
from src.services.query_service import QueryService
from src.services.chat_memory import ChatMemoryService
from src.services.feedback import FeedbackService
from src.rag.pipeline import RAGPipeline
from src.schemas.enums import QuerySource
from src.core.database import AsyncSessionLocal
from src.core.config import settings

router = Router()


async def keep_typing(chat_id: int, bot, stop_event: asyncio.Event):
    """
    Периодически отправляет typing indicator до тех пор, пока не будет остановлен.

    Typing indicator в Telegram живет 5 секунд, поэтому обновляем каждые 4 секунды.
    """
    try:
        while not stop_event.is_set():
            await bot.send_chat_action(chat_id, "typing")
            # Ждем 4 секунды или пока не придет сигнал остановки
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=4.0)
                break  # Если stop_event установлен, выходим
            except asyncio.TimeoutError:
                continue  # Timeout - продолжаем показывать typing
    except Exception as e:
        logger.debug(f"Typing task stopped: {e}")


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

        # Start continuous typing indicator
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            keep_typing(message.chat.id, message.bot, stop_typing)
        )

        try:
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

            # Process query synchronously using QueryService
            result = await query_service.process_query(
                question=question,
                user_id=str(message.from_user.id),
                source=QuerySource.TELEGRAM,
                enable_memory=True,
                enable_feedback=settings.TELEGRAM_ENABLE_FEEDBACK,
            )

            # Get answer and query_id from result
            current_text = result.answer
            query_id = result.query_id

            logger.info(f"Received answer: {len(current_text)} chars")

            # Log text before fix
            logger.info(f"Text BEFORE fix_html (first 300 chars): {current_text[:300]}")

            # Convert to HTML and fix formatting
            current_text = fix_html(current_text)

            # Log text after fix
            logger.info(f"Text AFTER fix_html (first 300 chars): {current_text[:300]}")

            # Stop typing indicator before sending answer
            stop_typing.set()
            try:
                await asyncio.wait_for(typing_task, timeout=1.0)
            except asyncio.TimeoutError:
                typing_task.cancel()

            # Split message if it's too long
            message_parts = split_message(current_text)

            if len(message_parts) == 1:
                # Single message - send directly with HTML formatting
                try:
                    sent_message = await message.answer(current_text, parse_mode="HTML")
                    logger.info("Final message sent with HTML formatting")
                except Exception as e:
                    logger.error(f"Failed to send message with HTML: {e}. Sending without formatting.")
                    # Fallback: send without formatting (explicitly set parse_mode=None)
                    try:
                        sent_message = await message.answer(current_text, parse_mode=None)
                        logger.info("Final message sent WITHOUT formatting (plain text)")
                    except Exception as e2:
                        logger.error(f"Failed to send message without formatting: {e2}")
            else:
                # Multiple messages needed
                logger.info(f"Splitting long answer into {len(message_parts)} messages")

                # Send all parts with HTML formatting
                for i, part in enumerate(message_parts):
                    part_suffix = f"\n\n<i>({i+1}/{len(message_parts)})</i>" if len(message_parts) > 1 else ""
                    await message.answer(part + part_suffix, parse_mode="HTML")

                # Keep reference to last message for feedback
                sent_message = None  # Feedback will be sent after all parts

            # Send feedback buttons if enabled and answer is valid
            if settings.TELEGRAM_ENABLE_FEEDBACK and should_request_feedback(current_text) and query_id:
                await message.answer(
                    "Оцените качество ответа:",
                    reply_markup=get_feedback_keyboard(query_id),
                )

            logger.info(f"Answer sent to user {message.from_user.id}, query_id: {query_id}")

        except Exception as e:
            # Stop typing on error
            stop_typing.set()
            typing_task.cancel()
            raise

    except Exception as e:
        logger.error("Error handling question: {}", e, exc_info=True)
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )
