"""Husk control plane FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from husk import __version__
from husk.auth.router import router as auth_router
from husk.auth.service import ApiKeyService
from husk.core import database as _db
from husk.core.config import settings
from husk.core.exceptions import install_handlers
from husk.core.logging import configure_logging
from husk.health.router import router as health_router
from husk.preview.router import router as preview_router
from husk.sandbox.router import router as sandbox_router
from husk.snapshot.router import router as snapshot_router
from husk.stub.router import router as stub_router
from husk.tasks.scheduler import start_scheduler, stop_scheduler
from husk.toolbox.router import router as toolbox_router
from husk.volume.router import router as volume_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await _db.init_db()
    await _bootstrap_root_apikey()
    scheduler = await start_scheduler()
    try:
        yield
    finally:
        await stop_scheduler(scheduler)


async def _bootstrap_root_apikey() -> None:
    """First start: ensure a root API key exists; print plaintext if newly generated."""
    import os

    # Read env at runtime (not via Settings cache) so test fixtures that set
    # HUSK_ROOT_API_KEY post-import still see it.
    configured = os.environ.get("HUSK_ROOT_API_KEY") or settings.root_api_key
    assert _db.session_factory is not None
    async with _db.session_factory() as db:
        plaintext = await ApiKeyService(db).ensure_root_key(configured)
    if plaintext and not configured:
        logger.warning("=" * 60)
        logger.warning("Husk auto-generated a root API key — save this NOW:")
        logger.warning("    {}", plaintext)
        logger.warning("It will not be shown again. Use HUSK_ROOT_API_KEY to pin one.")
        logger.warning("=" * 60)


app = FastAPI(
    title="Husk",
    version=__version__,
    lifespan=lifespan,
    description="Lightweight AI code sandbox runtime",
)

install_handlers(app)

app.include_router(auth_router, prefix="/api/api-keys", tags=["auth"])
app.include_router(sandbox_router, prefix="/api/sandbox", tags=["sandbox"])
app.include_router(snapshot_router, prefix="/api/snapshots", tags=["snapshot"])
app.include_router(volume_router, prefix="/api/volumes", tags=["volume"])
app.include_router(toolbox_router, prefix="/api/toolbox", tags=["toolbox"])
app.include_router(preview_router, prefix="/preview", tags=["preview"])
app.include_router(stub_router, prefix="/api", tags=["compat"])
app.include_router(health_router, prefix="/api/health", tags=["health"])

# Frontend static files (Phase 1.5 onwards). The directory is empty pre-build;
# StaticFiles tolerates that as long as the path exists.
app.mount(
    "/",
    StaticFiles(directory="husk/static/dashboard", html=True, check_dir=False),
    name="dashboard",
)
