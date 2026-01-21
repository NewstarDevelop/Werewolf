"""Async database connection and session management.

This module provides async database support using SQLAlchemy 2.0 async API.
Use get_async_db() for FastAPI dependency injection in async endpoints.
"""
from typing import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine database driver and pool settings based on URL
_is_sqlite = settings.DATABASE_URL_ASYNC.startswith("sqlite")
_pool_class = StaticPool if _is_sqlite else NullPool

# SQLite-specific connection args
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

# Create async engine
async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    echo=settings.DEBUG,  # Log SQL in debug mode
    poolclass=_pool_class,
    connect_args=_connect_args,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection: Get async database session.

    Usage:
        @router.get("/api/rooms")
        async def get_rooms(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Room))
            ...

    The session is automatically closed after the request.
    Rollback is performed if an exception occurs.
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


async def init_async_db():
    """Initialize async database (create tables if needed).

    This should be called during application startup for development.
    In production, use Alembic migrations instead.
    """
    from app.models.base import Base

    if settings.DEBUG:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Async database tables created (DEBUG mode)")


async def close_async_db():
    """Close async database connections.

    This should be called during application shutdown.
    """
    await async_engine.dispose()
    logger.info("Async database connections closed")


# Log configuration
logger.info(f"Async database configured: {settings.DATABASE_URL_ASYNC}")
