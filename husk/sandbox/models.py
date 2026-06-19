"""Sandbox ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from husk.core.database import Base
from husk.core.time import utcnow


class Sandbox(Base):
    __tablename__ = "sandbox"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True)
    container_id: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, default="creating")

    # Resources
    cpu: Mapped[int] = mapped_column(Integer, default=2)
    memory_mb: Mapped[int] = mapped_column(Integer, default=2048)
    disk_gb: Mapped[int] = mapped_column(Integer, default=10)

    # Metadata
    labels: Mapped[dict] = mapped_column(JSON, default=dict)

    # Multi-runner placeholders (always "default" in single-node mode)
    runner_id: Mapped[str] = mapped_column(String, default="default")
    region: Mapped[str] = mapped_column(String, default="default")

    # Auto-stop
    auto_stop_interval: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
