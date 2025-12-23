"""Inline keyboards for Telegram bot"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_feedback_keyboard(query_id: str) -> InlineKeyboardMarkup:
    """
    Create feedback keyboard with rating buttons

    Args:
        query_id: Query ID to associate with feedback

    Returns:
        InlineKeyboardMarkup with feedback buttons
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👍", callback_data=f"feedback:good:{query_id}"),
                InlineKeyboardButton(text="👌", callback_data=f"feedback:notbad:{query_id}"),
                InlineKeyboardButton(text="👎", callback_data=f"feedback:bad:{query_id}"),
            ]
        ]
    )
