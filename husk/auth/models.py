"""ApiKey ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from husk.core.database import Base
from husk.core.time import utcnow


class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    key_hash: Mapped[str] = mapped_column(String)  # argon2 hash
    prefix: Mapped[str] = mapped_column(String(12))  # for display: "hk_abc123…"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
