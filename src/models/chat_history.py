"""Chat history model for storing conversation context"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.models.base import Base


class ChatHistory(Base):
    """Chat history for maintaining conversation context"""

    __tablename__ = "chat_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sequence = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<ChatHistory(session_id={self.session_id}, role={self.role}, sequence={self.sequence})>"
