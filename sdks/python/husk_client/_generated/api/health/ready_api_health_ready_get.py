from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.ready_api_health_ready_get_response_ready_api_health_ready_get import ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet
from typing import cast



def _get_kwargs(
    
) -> dict[str, Any]:
    

    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/health/ready",
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet | None:
    if response.status_code == 200:
        response_200 = ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet.from_dict(response.json())



        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,

) -> Response[ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet]:
    """ Ready

     Readiness probe — checks Docker daemon reachability.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet]
     """


    kwargs = _get_kwargs(
        
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    *,
    client: AuthenticatedClient | Client,

) -> ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet | None:
    """ Ready

     Readiness probe — checks Docker daemon reachability.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet
     """


    return sync_detailed(
        client=client,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,

) -> Response[ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet]:
    """ Ready

     Readiness probe — checks Docker daemon reachability.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet]
     """


    kwargs = _get_kwargs(
        
    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    *,
    client: AuthenticatedClient | Client,

) -> ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet | None:
    """ Ready

     Readiness probe — checks Docker daemon reachability.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ReadyApiHealthReadyGetResponseReadyApiHealthReadyGet
     """


    return (await asyncio_detailed(
        client=client,

    )).parsed
