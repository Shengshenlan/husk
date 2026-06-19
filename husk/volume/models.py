"""Volume ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from husk.core.database import Base


class Volume(Base):
    __tablename__ = "volume"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    docker_volume: Mapped[str] = mapped_column(String)  # name in docker volume ls
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
