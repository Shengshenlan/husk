"""Preview FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.database import db_session

from .service import PreviewService


def preview_service(db: AsyncSession = Depends(db_session)) -> PreviewService:
    return PreviewService(db)
