"""Quickstart: spawn a sandbox via husk-client."""

from husk_client import AuthenticatedClient
from husk_client._generated.api.sandbox import (
    create_sandbox_api_sandbox_post,
    delete_sandbox_api_sandbox__sandbox_id__delete,
    list_sandboxes_api_sandbox_get,
)
from husk_client._generated.models import CreateRequest

client = AuthenticatedClient(
    base_url="http://localhost:8000",
    token="hk_xxxxxxxxxxxx",
)

sb = create_sandbox_api_sandbox_post.sync(
    client=client,
    body=CreateRequest(snapshot_id="alpine:3.20", cpu=1, memory_mb=512),
)
print(f"Created sandbox {sb.id} state={sb.state}")

all_sandboxes = list_sandboxes_api_sandbox_get.sync(client=client)
print(f"Total sandboxes: {len(all_sandboxes)}")

delete_sandbox_api_sandbox__sandbox_id__delete.sync_detailed(client=client, sandbox_id=sb.id)
print(f"Destroyed {sb.id}")
