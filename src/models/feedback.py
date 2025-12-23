"""Feedback model for storing user feedback on answers"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.models.base import Base


class Feedback(Base):
    """User feedback on query responses"""

    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    rating = Column(String(20), nullable=False)  # 'good', 'notbad', 'bad'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<Feedback(query_id={self.query_id}, rating={self.rating})>"
