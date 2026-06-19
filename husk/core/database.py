"""SQLAlchemy async engine, declarative Base, and session factory.

The engine and session factory are built lazily at first ``init_db()`` so that
process-wide environment variables (e.g. set by test fixtures) take effect
even if they were modified after the ``husk.core.config`` import.
"""

from __future__ import annotations

import os
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


_engine = None
session_factory: async_sessionmaker[AsyncSession] | None = None  # type: ignore[assignment]


def _resolve_db_url() -> str:
    return os.environ.get("HUSK_DB_URL") or settings.db_url


def _build() -> None:
    """(Re)build the engine + session factory from the current DB URL."""
    global _engine, session_factory  # noqa: PLW0603
    _engine = create_async_engine(_resolve_db_url(), echo=False, future=True)
    session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create all tables on first start. Replaced by Alembic in production paths."""
    if _engine is None:
        _build()
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields one session per request."""
    if session_factory is None:
        _build()
    assert session_factory is not None
    async with session_factory() as session:
        yield session
