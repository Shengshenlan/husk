from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.commit_sandbox_api_sandbox_sandbox_id_snapshot_post_response_commit_sandbox_api_sandbox_sandbox_id_snapshot_post import CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    sandbox_id: str,
    *,
    name: str,
    authorization: None | str | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization



    

    params: dict[str, Any] = {}

    params["name"] = name


    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}


    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/sandbox/{sandbox_id}/snapshot".format(sandbox_id=quote(str(sandbox_id), safe=""),),
        "params": params,
    }


    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost.from_dict(response.json())



        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    sandbox_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
    authorization: None | str | Unset = UNSET,

) -> Response[CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError]:
    """ Commit Sandbox

    Args:
        sandbox_id (str):
        name (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        sandbox_id=sandbox_id,
name=name,
authorization=authorization,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    sandbox_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
    authorization: None | str | Unset = UNSET,

) -> CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError | None:
    """ Commit Sandbox

    Args:
        sandbox_id (str):
        name (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError
     """


    return sync_detailed(
        sandbox_id=sandbox_id,
client=client,
name=name,
authorization=authorization,

    ).parsed

async def asyncio_detailed(
    sandbox_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
    authorization: None | str | Unset = UNSET,

) -> Response[CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError]:
    """ Commit Sandbox

    Args:
        sandbox_id (str):
        name (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        sandbox_id=sandbox_id,
name=name,
authorization=authorization,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    sandbox_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
    authorization: None | str | Unset = UNSET,

) -> CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError | None:
    """ Commit Sandbox

    Args:
        sandbox_id (str):
        name (str):
        authorization (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommitSandboxApiSandboxSandboxIdSnapshotPostResponseCommitSandboxApiSandboxSandboxIdSnapshotPost | HTTPValidationError
     """


    return (await asyncio_detailed(
        sandbox_id=sandbox_id,
client=client,
name=name,
authorization=authorization,

    )).parsed
