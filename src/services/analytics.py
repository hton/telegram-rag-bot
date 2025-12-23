"""Analytics service for usage statistics"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from loguru import logger

from src.models.query_log import QueryLog


class AnalyticsService:
    """Service for analytics and usage statistics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage_stats(
        self,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get usage statistics

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with usage stats
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Total queries
        total_query = select(func.count(QueryLog.id)).where(
            QueryLog.created_at >= since
        )
        total_result = await self.db.execute(total_query)
        total_queries = total_result.scalar()

        # Queries by source
        source_query = (
            select(QueryLog.source, func.count(QueryLog.id))
            .where(QueryLog.created_at >= since)
            .group_by(QueryLog.source)
        )
        source_result = await self.db.execute(source_query)
        by_source = dict(source_result.all())

        # Average processing time
        avg_time_query = select(func.avg(QueryLog.processing_time_ms)).where(
            QueryLog.created_at >= since
        )
        avg_time_result = await self.db.execute(avg_time_query)
        avg_processing_time = avg_time_result.scalar() or 0

        # Unique users
        unique_users_query = select(func.count(func.distinct(QueryLog.user_id))).where(
            and_(
                QueryLog.created_at >= since,
                QueryLog.user_id.isnot(None),
            )
        )
        unique_users_result = await self.db.execute(unique_users_query)
        unique_users = unique_users_result.scalar()

        return {
            "total_queries": total_queries,
            "by_source": by_source,
            "avg_processing_time_ms": round(avg_processing_time, 2),
            "unique_users": unique_users,
            "days": days,
        }

    async def get_popular_queries(
        self,
        limit: int = 10,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get most frequent queries"""
        since = datetime.utcnow() - timedelta(days=days)

        query = (
            select(
                QueryLog.question,
                func.count(QueryLog.id).label("count"),
            )
            .where(QueryLog.created_at >= since)
            .group_by(QueryLog.question)
            .order_by(func.count(QueryLog.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {"question": row.question, "count": row.count}
            for row in rows
        ]

    async def get_response_time_metrics(
        self,
        days: int = 7,
    ) -> Dict[str, Any]:
        """Get response time metrics"""
        since = datetime.utcnow() - timedelta(days=days)

        query = select(
            func.min(QueryLog.processing_time_ms),
            func.max(QueryLog.processing_time_ms),
            func.avg(QueryLog.processing_time_ms),
            func.percentile_cont(0.5).within_group(QueryLog.processing_time_ms),
            func.percentile_cont(0.95).within_group(QueryLog.processing_time_ms),
        ).where(QueryLog.created_at >= since)

        result = await self.db.execute(query)
        row = result.one()

        return {
            "min_ms": round(row[0], 2) if row[0] else 0,
            "max_ms": round(row[1], 2) if row[1] else 0,
            "avg_ms": round(row[2], 2) if row[2] else 0,
            "p50_ms": round(row[3], 2) if row[3] else 0,
            "p95_ms": round(row[4], 2) if row[4] else 0,
            "days": days,
        }
