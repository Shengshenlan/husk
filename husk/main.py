"""Husk control plane FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from husk import __version__
from husk.auth.router import router as auth_router
from husk.core.database import init_db
from husk.core.exceptions import install_handlers
from husk.core.logging import configure_logging
from husk.health.router import router as health_router
from husk.preview.router import router as preview_router
from husk.sandbox.router import router as sandbox_router
from husk.snapshot.router import router as snapshot_router
from husk.stub.router import router as stub_router
from husk.toolbox.router import router as toolbox_router
from husk.volume.router import router as volume_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await init_db()
    yield


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
