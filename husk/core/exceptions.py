"""Husk-specific exception hierarchy and global FastAPI handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class HuskError(Exception):
    """Base class for all Husk business exceptions."""

    status_code: int = 500
    code: str = "husk_error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


class NotFound(HuskError):
    status_code = 404
    code = "not_found"


class Conflict(HuskError):
    status_code = 409
    code = "conflict"


class Unauthorized(HuskError):
    status_code = 401
    code = "unauthorized"


def install_handlers(app: FastAPI) -> None:
    """Attach the global Husk exception → JSON handler."""

    @app.exception_handler(HuskError)
    async def _husk_handler(_: Request, exc: HuskError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )
