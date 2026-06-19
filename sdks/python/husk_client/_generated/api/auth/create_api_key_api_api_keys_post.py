from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.api_key_created_response import ApiKeyCreatedResponse
from ...models.create_api_key_request import CreateApiKeyRequest
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    *,
    body: CreateApiKeyRequest,
    authorization: None | str | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization



    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/api-keys",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> ApiKeyCreatedResponse | HTTPValidationError | None:
    if response.status_code == 201:
        response_201 = ApiKeyCreatedResponse.from_dict(response.json())



        return response_201

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[ApiKeyCreatedResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    authorization: None | str | Unset = UNSET,

) -> Response[ApiKeyCreatedResponse | HTTPValidationError]:
    """ Create Api Key

    Args:
        authorization (None | str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKeyCreatedResponse | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        body=body,
authorization=authorization,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    authorization: None | str | Unset = UNSET,

) -> ApiKeyCreatedResponse | HTTPValidationError | None:
    """ Create Api Key

    Args:
        authorization (None | str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKeyCreatedResponse | HTTPValidationError
     """


    return sync_detailed(
        client=client,
body=body,
authorization=authorization,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    authorization: None | str | Unset = UNSET,

) -> Response[ApiKeyCreatedResponse | HTTPValidationError]:
    """ Create Api Key

    Args:
        authorization (None | str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ApiKeyCreatedResponse | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        body=body,
authorization=authorization,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: CreateApiKeyRequest,
    authorization: None | str | Unset = UNSET,

) -> ApiKeyCreatedResponse | HTTPValidationError | None:
    """ Create Api Key

    Args:
        authorization (None | str | Unset):
        body (CreateApiKeyRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ApiKeyCreatedResponse | HTTPValidationError
     """


    return (await asyncio_detailed(
        client=client,
body=body,
authorization=authorization,

    )).parsed
