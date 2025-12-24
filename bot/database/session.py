"""Database session management with connection pooling."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from bot.config import settings
from bot.utils.logger import logger


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker | None = None
    
    def init(self) -> None:
        """Initialize database engine and session factory."""
        if settings.database_url.startswith("sqlite"):
            # SQLite doesn't support connection pooling
            self._engine = create_async_engine(
                settings.database_url,
                echo=settings.log_level == "DEBUG",
                poolclass=NullPool,
            )
        else:
            # PostgreSQL with connection pooling
            self._engine = create_async_engine(
                settings.database_url,
                echo=settings.log_level == "DEBUG",
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
        
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        
        logger.info("database_initialized", url=settings.database_url)
    
    async def dispose(self) -> None:
        """Dispose database engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("database_disposed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope for database operations."""
        if not self._session_factory:
            raise RuntimeError("DatabaseManager not initialized")
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            await session.close()
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if not self._engine:
            raise RuntimeError("DatabaseManager not initialized")
        return self._engine


# Global database manager instance
db_manager = DatabaseManager()
