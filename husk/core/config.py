"""Husk control plane configuration."""

from __future__ import annotations

import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration. Environment variables prefixed with HUSK_."""

    model_config = SettingsConfigDict(env_prefix="HUSK_", env_file=".env", extra="ignore")

    # ── Core ──
    data_dir: str = "/data"
    db_url: str = "sqlite+aiosqlite:////data/husk.db"
    listen_host: str = "0.0.0.0"
    listen_port: int = 8000
    log_level: str = "info"

    # ── Docker ──
    docker_host: str = "unix:///var/run/docker.sock"
    default_network: str = "bridge"
    default_image: str = "python:3.12"

    # ── Daemon ──
    daemon_bin: str = "/app/embedded/daemon-amd64"
    daemon_port: int = 8080
    daemon_target: str = "/opt/husk/daemon"

    # ── Schedulers ──
    auto_stop_enabled: bool = True
    auto_stop_check_interval: int = 30  # seconds
    reaper_interval: int = 60  # seconds

    # ── Auth ──
    root_api_key: str | None = None  # 启动时若未设则自动生成
    preview_jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32))


settings = Settings()
