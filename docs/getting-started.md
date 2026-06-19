# Getting started with Husk

> 5-minute path to a running sandbox. Real content lands in M5; this is a placeholder.

## Prerequisites

- Docker (rootful for now; rootless support is on the roadmap)
- ~200 MB disk for the Husk image + your sandbox snapshots

## Quickstart (Docker)

```bash
docker run -d --name husk \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v husk-data:/data \
  husk/husk:latest

# get the auto-generated root API key
docker logs husk | grep "root API key"

# create a sandbox
curl -X POST http://localhost:8000/api/sandbox \
  -H "Authorization: Bearer hk_xxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"snapshot_id":"py-3.12","cpu":2,"memory_mb":2048}'
```

## From source

```bash
git clone https://github.com/your-org/husk
cd husk
uv sync
uv run alembic upgrade head
uv run husk serve
```

Then open <http://localhost:8000/docs> for the OpenAPI explorer.

## Next steps

- [Configuration](./configuration.md)
- [SDK quickstart (Python)](./sdks/python.md)
- [Architecture](../ARCHITECTURE.md)
