"""
Database configuration and session management
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

from src.core.config import settings

# Ensure DATABASE_URL is not None
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured")

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
    future=True,
    poolclass=StaticPool,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for all database models
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """
    Create all database tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """
    Drop all database tables
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
