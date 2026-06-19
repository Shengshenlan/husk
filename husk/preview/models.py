"""Preview-token ORM model (signed URLs for sandbox port access)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from husk.core.database import Base
from husk.core.time import utcnow


class PreviewToken(Base):
    __tablename__ = "preview_token"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sandbox_id: Mapped[str] = mapped_column(String, index=True)
    port: Mapped[int] = mapped_column(Integer)
    token: Mapped[str] = mapped_column(String, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
