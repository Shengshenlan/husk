"""Auth HTTP router."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, status
from jose import jwt

from husk.core.config import settings

from .dependencies import apikey_service, current_apikey
from .exceptions import InvalidCredentials
from .schemas import (
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    CreateApiKeyRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from .service import ApiKeyService

router = APIRouter()
session_router = APIRouter()


@router.get("", response_model=list[ApiKeyResponse], dependencies=[Depends(current_apikey)])
async def list_api_keys(service: ApiKeyService = Depends(apikey_service)) -> list[ApiKeyResponse]:
    return [ApiKeyResponse.model_validate(k) for k in await service.list()]


@router.post(
    "",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_apikey)],
)
async def create_api_key(
    body: CreateApiKeyRequest,
    service: ApiKeyService = Depends(apikey_service),
) -> ApiKeyCreatedResponse:
    row, plaintext = await service.create(body.name)
    return ApiKeyCreatedResponse.model_validate({**row.__dict__, "key": plaintext})


@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_apikey)],
)
async def revoke_api_key(
    name: str,
    service: ApiKeyService = Depends(apikey_service),
) -> None:
    await service.revoke(name)


@session_router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    if body.username != settings.admin_username or body.password != settings.admin_password:
        raise InvalidCredentials("username or password incorrect")
    exp = datetime.now(UTC) + timedelta(days=7)
    token = jwt.encode(
        {"sub": settings.admin_username, "type": "session", "exp": exp},
        settings.preview_jwt_secret,
        algorithm="HS256",
    )
    return LoginResponse(access_token=token)


@session_router.get("/me", response_model=UserResponse, dependencies=[Depends(current_apikey)])
async def me() -> UserResponse:
    return UserResponse(username=settings.admin_username)
