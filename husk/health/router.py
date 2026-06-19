"""Health check endpoints — no auth required."""

from __future__ import annotations

from fastapi import APIRouter

from husk import __version__
from husk.core.deps import docker_client

router = APIRouter()


@router.get("")
async def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/ready")
async def ready() -> dict:
    """Readiness probe — checks Docker daemon reachability."""
    try:
        docker_client().ping()
        docker_ok = True
    except Exception:
        docker_ok = False
    return {"status": "ok" if docker_ok else "degraded", "docker": docker_ok}
