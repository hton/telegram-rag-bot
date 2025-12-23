"""Health check routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.core.database import get_db
from src.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "telegram-rag-bot",
        "version": "0.1.0",
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check (includes database connectivity)"""
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "checks": {
                "database": "connected",
            }
        }
    except Exception as e:
        return {
            "status": "not ready",
            "checks": {
                "database": f"error: {str(e)}",
            }
        }


@router.get("/health/live")
async def liveness_check():
    """Liveness check"""
    return {"status": "alive"}
