"""Snapshot ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from husk.core.database import Base
from husk.core.time import utcnow


class Snapshot(Base):
    __tablename__ = "snapshot"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    image_ref: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String, default="pulling")  # pulling/active/failed
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
