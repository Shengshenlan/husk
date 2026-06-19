from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.issue_preview_request import IssuePreviewRequest
from ...models.preview_url_response import PreviewUrlResponse
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    *,
    body: IssuePreviewRequest,
    authorization: None | str | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(authorization, Unset):
        headers["authorization"] = authorization



    

    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/preview/issue",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> HTTPValidationError | PreviewUrlResponse | None:
    if response.status_code == 200:
        response_200 = PreviewUrlResponse.from_dict(response.json())



        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[HTTPValidationError | PreviewUrlResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: IssuePreviewRequest,
    authorization: None | str | Unset = UNSET,

) -> Response[HTTPValidationError | PreviewUrlResponse]:
    """ Issue a signed preview URL for a sandbox port

    Args:
        authorization (None | str | Unset):
        body (IssuePreviewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PreviewUrlResponse]
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
    body: IssuePreviewRequest,
    authorization: None | str | Unset = UNSET,

) -> HTTPValidationError | PreviewUrlResponse | None:
    """ Issue a signed preview URL for a sandbox port

    Args:
        authorization (None | str | Unset):
        body (IssuePreviewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PreviewUrlResponse
     """


    return sync_detailed(
        client=client,
body=body,
authorization=authorization,

    ).parsed

async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: IssuePreviewRequest,
    authorization: None | str | Unset = UNSET,

) -> Response[HTTPValidationError | PreviewUrlResponse]:
    """ Issue a signed preview URL for a sandbox port

    Args:
        authorization (None | str | Unset):
        body (IssuePreviewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | PreviewUrlResponse]
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
    body: IssuePreviewRequest,
    authorization: None | str | Unset = UNSET,

) -> HTTPValidationError | PreviewUrlResponse | None:
    """ Issue a signed preview URL for a sandbox port

    Args:
        authorization (None | str | Unset):
        body (IssuePreviewRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | PreviewUrlResponse
     """


    return (await asyncio_detailed(
        client=client,
body=body,
authorization=authorization,

    )).parsed
