"""Auth schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateApiKeyRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None = None

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned exactly once on creation; includes the plaintext key."""

    key: str
