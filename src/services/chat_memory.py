"""Chat memory service for maintaining conversation context"""
import re
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from src.models.chat_history import ChatHistory
from src.core.config import settings


def extract_summary(answer: str) -> str:
    """
    Извлекает краткий ответ из структурированного HTML-ответа

    Формат ответа:
    <b>Краткий ответ</b>
    [1-2 предложения]

    <b>Подробное объяснение</b>
    ...

    Args:
        answer: Полный HTML-ответ ассистента

    Returns:
        Краткий ответ (summary) без HTML-тегов блока
    """
    # Ищем текст между "</b>" после "Краткий ответ" и следующим "<b>"
    pattern = r'<b>Краткий ответ</b>\s*(.*?)\s*<b>'
    match = re.search(pattern, answer, re.DOTALL | re.IGNORECASE)

    if match:
        summary = match.group(1).strip()
        # Убираем множественные переводы строк
        summary = re.sub(r'\n\n+', '\n', summary)
        logger.debug(f"Extracted summary: {len(summary)} chars from {len(answer)} chars answer")
        return summary

    # Fallback - если структура не найдена, берем первые 200 символов
    # (для обратной совместимости или нестандартных ответов)
    logger.warning(f"Could not extract summary, using fallback (first 200 chars)")
    return answer[:200] + "..."


class ChatMemoryService:
    """
    Service for managing chat history and conversation context

    Stores messages in PostgreSQL and retrieves recent context for RAG
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.context_window = settings.CONTEXT_WINDOW

    async def get_history(
        self,
        session_id: str,
        limit: int = None,
    ) -> List[Dict[str, str]]:
        """
        Get chat history for a session

        Retrieves messages and truncates assistant responses to summaries for token
        efficiency when sending context to GPT. Full answers remain in database for
        feedback analysis and future Q&A caching.

        Args:
            session_id: Session identifier
            limit: Max number of messages (default: from config)

        Returns:
            List of messages in format [{"role": "user", "content": "..."}, ...]
            Assistant messages are truncated to "Краткий ответ" section
        """
        limit = limit or self.context_window

        query = (
            select(ChatHistory)
            .where(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.sequence.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.scalars().all()

        # Reverse to get chronological order and truncate assistant messages
        history = []
        for row in reversed(rows):
            content = row.content
            # Truncate assistant messages to summary for GPT context efficiency
            if row.role == "assistant":
                content = extract_summary(content)

            history.append({"role": row.role, "content": content})

        logger.debug(f"Retrieved {len(history)} messages for session {session_id}")
        return history

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Add a message to chat history

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        # Get current max sequence number
        query = select(func.max(ChatHistory.sequence)).where(
            ChatHistory.session_id == session_id
        )
        result = await self.db.execute(query)
        max_sequence = result.scalar() or 0

        # Create new message
        message = ChatHistory(
            session_id=session_id,
            role=role,
            content=content,
            sequence=max_sequence + 1,
        )

        self.db.add(message)
        await self.db.commit()

        logger.debug(f"Added {role} message to session {session_id}")

    async def add_assistant_message(
        self,
        session_id: str,
        full_answer: str,
    ) -> None:
        """
        Add assistant message to chat history

        Saves the full HTML-formatted answer to chat history. Summary extraction
        happens during retrieval (get_history) to reduce token usage when sending
        context to GPT, while preserving full answers for feedback analysis.

        Args:
            session_id: Session identifier
            full_answer: Full HTML-formatted answer from RAG
        """
        # Save full answer to history (summary extraction happens on retrieval)
        await self.add_message(session_id, "assistant", full_answer)

        logger.debug(
            f"Added assistant message to session {session_id} "
            f"(full answer: {len(full_answer)} chars)"
        )

    async def clear_history(self, session_id: str) -> None:
        """Clear all history for a session"""
        query = select(ChatHistory).where(ChatHistory.session_id == session_id)
        result = await self.db.execute(query)
        messages = result.scalars().all()

        for message in messages:
            await self.db.delete(message)

        await self.db.commit()
        logger.info(f"Cleared history for session {session_id}")
