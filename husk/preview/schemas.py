"""Preview HTTP schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PreviewUrlResponse(BaseModel):
    url: str
    token: str
    expires_at: datetime
