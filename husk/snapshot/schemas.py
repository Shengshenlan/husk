"""Snapshot HTTP schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateSnapshotRequest(BaseModel):
    name: str
    image_ref: str  # e.g. "python:3.12" or "myorg/myimage:tag"


class SnapshotResponse(BaseModel):
    id: str
    name: str
    image_ref: str
    state: str
    size_bytes: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
