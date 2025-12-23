"""Query log model for tracking all RAG queries"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Boolean, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.models.base import Base


class QueryLog(Base):
    """Log of all RAG queries for analytics and monitoring"""

    __tablename__ = "query_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    user_id = Column(String(255), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)

    source = Column(String(50), nullable=False, index=True)  # 'telegram' or 'api'
    processing_time_ms = Column(Float, nullable=False)

    feedback_enabled = Column(Boolean, default=True)
    feedback = Column(String(20), nullable=True)  # 'good', 'notbad', 'bad'

    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<QueryLog(id={self.id}, source={self.source}, question={self.question[:50]}...)>"
