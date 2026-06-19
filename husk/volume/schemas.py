"""Volume HTTP schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateVolumeRequest(BaseModel):
    name: str


class VolumeResponse(BaseModel):
    id: str
    name: str
    docker_volume: str
    created_at: datetime

    class Config:
        from_attributes = True
