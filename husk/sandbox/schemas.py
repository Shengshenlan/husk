"""Sandbox HTTP schemas (pydantic)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .constants import DEFAULT_CPU, DEFAULT_DISK_GB, DEFAULT_MEMORY_MB


class CreateRequest(BaseModel):
    name: str | None = None
    snapshot_id: str | None = None
    cpu: int = Field(default=DEFAULT_CPU, ge=1, le=64)
    memory_mb: int = Field(default=DEFAULT_MEMORY_MB, ge=128, le=131072)
    disk_gb: int = Field(default=DEFAULT_DISK_GB, ge=1, le=10240)
    labels: dict[str, str] = Field(default_factory=dict)
    auto_stop_interval: int | None = None


class ResizeRequest(BaseModel):
    cpu: int | None = None
    memory_mb: int | None = None
    disk_gb: int | None = None


class SandboxResponse(BaseModel):
    id: str
    name: str
    snapshot_id: str | None = None
    state: str
    cpu: int
    memory_mb: int
    disk_gb: int
    labels: dict[str, str]
    runner_id: str
    region: str
    auto_stop_interval: int | None = None
    last_activity_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
