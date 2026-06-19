from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.snapshot_response import SnapshotResponse
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    snapshot_id: str,
    *,
    authorization: None | str | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization



    

    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/snapshots/{snapshot_id}".format(snapshot_id=quote(str(snapshot_id), safe=""),),
    }


    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> HTTPValidationError | SnapshotResponse | None:
    if response.status_code == 200:
        response_200 = SnapshotResponse.from_dict(response.json())



        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[HTTPValidationError | SnapshotResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    snapshot_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,

) -> Response[HTTPValidationError | SnapshotResponse]:
    """ Get Snapshot

    Args:
        snapshot_id (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SnapshotResponse]
     """


    kwargs = _get_kwargs(
        snapshot_id=snapshot_id,
authorization=authorization,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    snapshot_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,

) -> HTTPValidationError | SnapshotResponse | None:
    """ Get Snapshot

    Args:
        snapshot_id (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SnapshotResponse
     """


    return sync_detailed(
        snapshot_id=snapshot_id,
client=client,
authorization=authorization,

    ).parsed

async def asyncio_detailed(
    snapshot_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,

) -> Response[HTTPValidationError | SnapshotResponse]:
    """ Get Snapshot

    Args:
        snapshot_id (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SnapshotResponse]
     """


    kwargs = _get_kwargs(
        snapshot_id=snapshot_id,
authorization=authorization,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    snapshot_id: str,
    *,
    client: AuthenticatedClient | Client,
    authorization: None | str | Unset = UNSET,

) -> HTTPValidationError | SnapshotResponse | None:
    """ Get Snapshot

    Args:
        snapshot_id (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SnapshotResponse
     """


    return (await asyncio_detailed(
        snapshot_id=snapshot_id,
client=client,
authorization=authorization,

    )).parsed
