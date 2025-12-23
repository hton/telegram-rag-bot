"""Database configuration and session management"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool
from loguru import logger

from src.core.config import settings

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.DEBUG,
    poolclass=NullPool if settings.DEBUG else None,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables if needed)"""
    from src.models.base import Base

    logger.info("Initializing database...")

    async with engine.begin() as conn:
        # Import all models to register them
        from src.models import (
            chat_history,
            feedback,
            query_log,
        )

        # Create tables (only those not already created)
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connections"""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")
