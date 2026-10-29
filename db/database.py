"""Pulse2026 Asynchronous Database Session Engine."""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

DEFAULT_PG_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/pulse2026"
DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///pulse2026.db"

# Allow selecting database URL via environment or fallback
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_PG_URL)

try:
    if DATABASE_URL.startswith("postgresql+asyncpg"):
        import asyncpg  # verify availability
        engine = create_async_engine(
            DATABASE_URL,
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_pre_ping=True,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    else:
        engine = create_async_engine(
            DATABASE_URL,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
except (ImportError, ModuleNotFoundError):
    # Fallback to aiosqlite for hermetic testing and environments without asyncpg
    DATABASE_URL = os.getenv("TEST_DATABASE_URL", DEFAULT_SQLITE_URL)
    engine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI async dependency generator for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_models(target_engine=None) -> None:
    """Create all database tables using the declarative metadata."""
    eng = target_engine or engine
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
