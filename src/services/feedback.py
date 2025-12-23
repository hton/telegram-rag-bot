"""Feedback service for collecting user feedback"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger

from src.models.feedback import Feedback
from src.models.query_log import QueryLog
from src.core.metrics import feedback_counter


class FeedbackService:
    """Service for managing user feedback on query responses"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_feedback(
        self,
        query_id: str,
        rating: str,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        """
        Save user feedback for a query

        Args:
            query_id: Query ID
            rating: Feedback rating ('good', 'notbad', 'bad')
            user_id: User identifier
            comment: Optional comment
        """
        # Create feedback record
        feedback = Feedback(
            query_id=query_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )

        self.db.add(feedback)

        # Update query log with feedback
        query = select(QueryLog).where(QueryLog.id == query_id)
        result = await self.db.execute(query)
        query_log = result.scalar_one_or_none()

        if query_log:
            query_log.feedback = rating

        await self.db.commit()

        # Update metrics
        feedback_counter.labels(rating=rating).inc()

        logger.info(f"Saved feedback for query {query_id}: {rating}")

    async def get_feedback_stats(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get feedback statistics

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with feedback stats
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Count by rating
        query = (
            select(Feedback.rating, func.count(Feedback.id))
            .where(Feedback.created_at >= since)
            .group_by(Feedback.rating)
        )

        result = await self.db.execute(query)
        rating_counts = dict(result.all())

        total = sum(rating_counts.values())

        stats = {
            "total_feedback": total,
            "good": rating_counts.get("good", 0),
            "notbad": rating_counts.get("notbad", 0),
            "bad": rating_counts.get("bad", 0),
            "good_percentage": (rating_counts.get("good", 0) / total * 100) if total > 0 else 0,
            "days": days,
        }

        return stats

    async def get_recent_feedback(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent feedback entries"""
        query = (
            select(Feedback)
            .order_by(Feedback.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        feedbacks = result.scalars().all()

        return [
            {
                "query_id": str(fb.query_id),
                "rating": fb.rating,
                "user_id": fb.user_id,
                "comment": fb.comment,
                "created_at": fb.created_at.isoformat(),
            }
            for fb in feedbacks
        ]
