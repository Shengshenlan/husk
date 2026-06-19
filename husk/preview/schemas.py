"""Preview HTTP schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class IssuePreviewRequest(BaseModel):
    sandbox_id: str
    port: int
    ttl_seconds: int = 3600


class PreviewUrlResponse(BaseModel):
    url: str
    token: str
    expires_at: datetime
