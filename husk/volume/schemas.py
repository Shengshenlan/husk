"""Volume HTTP schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CreateVolumeRequest(BaseModel):
    name: str


class VolumeResponse(BaseModel):
    id: str
    name: str
    docker_volume: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
