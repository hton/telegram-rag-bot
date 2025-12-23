"""Admin API routes"""
from typing import Optional
from fastapi import APIRouter, Depends
from loguru import logger

from src.api.dependencies import get_analytics_service, get_feedback_service
from src.services.analytics import AnalyticsService
from src.services.feedback import FeedbackService

router = APIRouter()


@router.get("/stats")
async def get_stats(
    days: int = 30,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get usage statistics"""
    try:
        stats = await analytics_service.get_usage_stats(days=days)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise


@router.get("/feedback/stats")
async def get_feedback_stats(
    days: int = 30,
    feedback_service: FeedbackService = Depends(get_feedback_service),
):
    """Get feedback statistics"""
    try:
        stats = await feedback_service.get_feedback_stats(days=days)
        return stats
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise


@router.get("/feedback/recent")
async def get_recent_feedback(
    limit: int = 10,
    feedback_service: FeedbackService = Depends(get_feedback_service),
):
    """Get recent feedback entries"""
    try:
        feedback = await feedback_service.get_recent_feedback(limit=limit)
        return {"feedback": feedback}
    except Exception as e:
        logger.error(f"Error getting recent feedback: {e}")
        raise


@router.get("/queries/popular")
async def get_popular_queries(
    limit: int = 10,
    days: int = 30,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get most popular queries"""
    try:
        queries = await analytics_service.get_popular_queries(limit=limit, days=days)
        return {"queries": queries}
    except Exception as e:
        logger.error(f"Error getting popular queries: {e}")
        raise


@router.get("/performance")
async def get_performance_metrics(
    days: int = 7,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get performance metrics"""
    try:
        metrics = await analytics_service.get_response_time_metrics(days=days)
        return metrics
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise
