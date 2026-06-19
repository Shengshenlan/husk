"""Auth HTTP router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from .dependencies import apikey_service, current_apikey
from .schemas import ApiKeyCreatedResponse, ApiKeyResponse, CreateApiKeyRequest
from .service import ApiKeyService

router = APIRouter()


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
