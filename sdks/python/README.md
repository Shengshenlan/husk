# husk-client

Auto-generated Python client for the [Husk](https://github.com/your-org/husk)
control plane API. **Do not edit `husk_client/_generated/` by hand** —
regenerate via `scripts/gen-sdk-clients.sh` from the repo root.

## Install

```bash
pip install husk-client
```

## Quickstart

```python
from husk_client import AuthenticatedClient
from husk_client.api.sandbox import create_sandbox
from husk_client.models import CreateRequest

client = AuthenticatedClient(
    base_url="http://localhost:8000",
    token="hk_xxxxxxxxxxxx",
)

sb = create_sandbox.sync(
    client=client,
    body=CreateRequest(snapshot_id="py-3.12", cpu=2, memory_mb=2048),
)
print(sb.id, sb.state)
```

## Status

Phase 1.7 (M5.8 – M5.10). Currently scaffold-only.

## License

MIT
