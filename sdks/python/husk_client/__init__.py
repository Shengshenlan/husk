"""husk-client — Python client for the Husk control plane.

Auto-generated from the OpenAPI schema. To regenerate, run from the repo root::

    ./scripts/gen-sdk-clients.sh

Quickstart::

    from husk_client._generated import AuthenticatedClient
    from husk_client._generated.api.sandbox import create_sandbox_api_sandbox_post
    from husk_client._generated.models import CreateRequest

    client = AuthenticatedClient(
        base_url="http://localhost:8000",
        token="hk_xxxxxxxxxxxx",
    )
    sb = create_sandbox_api_sandbox_post.sync(
        client=client,
        body=CreateRequest(snapshot_id="alpine:3.20", cpu=1, memory_mb=512),
    )
    print(sb.id, sb.state)
"""

from ._generated import AuthenticatedClient, Client

__version__ = "0.0.1"

__all__ = ["AuthenticatedClient", "Client", "__version__"]
