"""SQLAlchemy async engine, declarative Base, and session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Common SQLAlchemy declarative base. All ORM models inherit from this."""


_engine = create_async_engine(settings.db_url, echo=False, future=True)
session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create all tables on first start. Replaced by Alembic in production paths."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields one session per request."""
    async with session_factory() as session:
        yield session
