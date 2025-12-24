"""Callback query handlers for Telegram bot"""
from aiogram import Router, F, types
from loguru import logger

from src.services.feedback import FeedbackService
from src.core.database import AsyncSessionLocal

router = Router()


@router.callback_query(F.data.startswith("feedback:"))
async def handle_feedback(callback: types.CallbackQuery):
    """Handle feedback button clicks"""
    try:
        # Parse callback data: feedback:rating:query_id
        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("Неверный формат обратной связи")
            return

        rating = parts[1]  # good, notbad, bad
        query_id = parts[2]

        # Save feedback
        async with AsyncSessionLocal() as db:
            feedback_service = FeedbackService(db)
            await feedback_service.save_feedback(
                query_id=query_id,
                rating=rating,
                user_id=str(callback.from_user.id),
            )

        # Send confirmation
        rating_text = {
            "good": "👍 Отлично!",
            "notbad": "👌 Неплохо",
            "bad": "👎 Плохо",
        }.get(rating, "Спасибо!")

        await callback.answer(f"{rating_text} Спасибо за обратную связь!")

        # Edit message to remove buttons
        await callback.message.edit_text(
            f"✅ Вы оценили ответ: {rating_text}",
            reply_markup=None,
        )

        logger.info(f"Feedback saved: {rating} for query {query_id} from user {callback.from_user.id}")

    except Exception as e:
        logger.error("Error handling feedback: {}", e, exc_info=True)
        await callback.answer("Ошибка при сохранении обратной связи")
