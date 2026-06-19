"""Common FastAPI dependencies shared across feature domains."""

from __future__ import annotations

from .config import Settings, settings


def get_settings() -> Settings:
    """Singleton settings dependency."""
    return settings


# DockerClient singleton placeholder. Real implementation in core.docker_client.
_docker_singleton = None


def docker_client():
    """Return the singleton DockerClient. Lazily initialized."""
    global _docker_singleton
    if _docker_singleton is None:
        from .docker_client import DockerClient

        _docker_singleton = DockerClient(settings.docker_host)
    return _docker_singleton
