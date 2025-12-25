"""Message handlers for Telegram bot"""
from aiogram import Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import time

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
            # Note: We accumulate chunks but don't send preview to avoid ugly HTML tags display
            # We periodically send typing indicator to show the user that bot is working
            current_text = ""
            query_id = None
            last_typing = time.time()
            typing_interval = 4.0  # Send typing action every 4 seconds (Telegram typing lasts 5 sec)

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

                # Accumulate chunks (no preview sending)
                current_text += chunk

                # Keep typing indicator alive
                if time.time() - last_typing > typing_interval:
                    await message.bot.send_chat_action(message.chat.id, "typing")
                    last_typing = time.time()

            # Final update with complete answer
            logger.info(f"Received complete answer: {len(current_text)} chars")

            # Log text before fix
            logger.info(f"Text BEFORE fix_html (first 300 chars): {current_text[:300]}")

            # Convert to HTML and fix formatting
            current_text = fix_html(current_text)

            # Log text after fix
            logger.info(f"Text AFTER fix_html (first 300 chars): {current_text[:300]}")

            # Debug: log text around potential error position (byte 606)
            if len(current_text) > 606:
                start = max(0, 500)  # Start earlier to see full context
                end = min(len(current_text), 900)  # Show 400 chars window around 606
                logger.info(f"Text from byte 500 to 900 AFTER fix_markdown:")
                logger.info(f"{repr(current_text[start:end])}")
                logger.info(f"Character at 606: {repr(current_text[606])}")

                # Count markdown markers to detect imbalance
                text_until_606 = current_text[:607]
                bold_count = text_until_606.count('**')
                logger.info(f"Bold markers (**) up to byte 606: {bold_count} (should be even)")

                # Show all bold marker positions
                import re
                bold_positions = [m.start() for m in re.finditer(r'\*\*', current_text[:700])]
                logger.info(f"Bold marker positions in first 700 chars: {bold_positions}")

                # Log actual BYTES around position 606 to debug UTF-8 encoding
                text_bytes = current_text.encode('utf-8')
                if len(text_bytes) > 606:
                    logger.info(f"Total text length: {len(current_text)} chars, {len(text_bytes)} bytes")
                    start_byte = max(0, 580)
                    end_byte = min(len(text_bytes), 650)
                    bytes_window = text_bytes[start_byte:end_byte]
                    logger.info(f"Bytes {start_byte} to {end_byte}: {bytes_window}")
                    logger.info(f"Byte at 606: {text_bytes[606:607]} (hex: {text_bytes[606:607].hex()})")
                    # Decode bytes around 606 to see the text
                    try:
                        decoded = bytes_window.decode('utf-8')
                        logger.info(f"Decoded text from bytes {start_byte}-{end_byte}: {repr(decoded)}")
                    except:
                        logger.info(f"Failed to decode bytes around 606")

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
        logger.error("Error handling question: {}", e, exc_info=True)
        await message.answer(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )
