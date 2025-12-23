"""FastAPI dependencies"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.query_service import QueryService
from src.services.chat_memory import ChatMemoryService
from src.services.feedback import FeedbackService
from src.services.analytics import AnalyticsService
from src.rag.pipeline import RAGPipeline


async def get_query_service(
    db: AsyncSession = Depends(get_db),
) -> QueryService:
    """Get QueryService instance"""
    rag_pipeline = RAGPipeline(db)
    memory_service = ChatMemoryService(db)
    feedback_service = FeedbackService(db)

    return QueryService(db, rag_pipeline, memory_service, feedback_service)


async def get_analytics_service(
    db: AsyncSession = Depends(get_db),
) -> AnalyticsService:
    """Get AnalyticsService instance"""
    return AnalyticsService(db)


async def get_feedback_service(
    db: AsyncSession = Depends(get_db),
) -> FeedbackService:
    """Get FeedbackService instance"""
    return FeedbackService(db)
