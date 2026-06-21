# Husk

> **The husk is the boundary. What runs inside is yours.**

Husk is a lightweight AI code sandbox runtime — giving Agents and SDKs high-level capabilities like "create containers, run code, operate files, use Git." **MIT-licensed, single image, single process, one `docker run` to launch.**

---

## Installation & Quick Start

**Docker only.**

```bash
docker run -d --name husk \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v husk-data:/data \
  -e HUSK_ADMIN_USERNAME=admin \
  -e HUSK_ADMIN_PASSWORD=your-password \
  husk/husk:latest
```

Open <http://localhost:8000>, log in with the credentials you set above, and manage sandboxes and API keys from the Dashboard.

> To run from source, see [docs/getting-started.md](./docs/getting-started.md).

---

## SDK Usage

### Python SDK (recommended)

```bash
pip install husk-client
```

```python
from husk_client import Husk

husk = Husk(base_url="http://localhost:8000", api_key="hk_...")
sandbox = husk.create(image="python:3.12-slim")

# Execute commands
result = sandbox.process.execute("python -c 'print(1+2)'")
print(result.stdout)   # "3\n"

# Run code snippets
result = sandbox.process.code_run("print('hello')")
print(result.stdout)   # "hello\n"

# File operations
sandbox.fs.upload(path="/workspace/x.txt", content=b"hello")
files = sandbox.fs.list("/workspace")
content = sandbox.fs.download("/workspace/x.txt")

# Destroy when done
sandbox.destroy()
```

Create API keys from the Dashboard's "API Keys" page, or generate them via CLI: `husk apikey create <name>`.

### LangChain Integration

Use with [Deep Agents](https://github.com/langchain-ai/deepagents):

```bash
pip install langchain-husk
```

```python
from husk_client import Husk
from langchain_husk import HuskSandbox

# Create a sandbox first
sandbox = Husk(base_url="http://localhost:8000", api_key="hk_...").create(
    image="python:3.12-slim",
)

# Wrap as a Deep Agents backend
backend = HuskSandbox(sandbox=sandbox, timeout=300)
result = backend.execute("python -c 'print(1+2)'")
print(result.output, result.exit_code)

# Wire into Deep Agents
# from deepagents import DeepAgent
# agent = DeepAgent(backend=backend, ...)

sandbox.destroy()
```

### Other Language SDKs

| Language | Package | Install |
|---|---|---|
| Python | `husk-client` | `pip install husk-client` |
| TypeScript | `@husk/client` | `npm install @husk/client` |
| Go | `github.com/husklabs/husk-go` | `go get github.com/husklabs/husk-go` |

All SDKs are auto-generated from the control plane's OpenAPI spec. Run `./scripts/gen-sdk-clients.sh` to regenerate after schema changes.

---

## Configuration

Core environment variables:

| Variable | Description |
|---|---|
| `HUSK_ADMIN_USERNAME` | Dashboard login username (default: `admin`) |
| `HUSK_ADMIN_PASSWORD` | **Required.** Dashboard login password |
| `HUSK_DATA_DIR` | Data directory (default: `/data`) |
| `HUSK_DB_URL` | Database URL (default: SQLite; Postgres supported) |
| `HUSK_LISTEN_HOST` / `HUSK_LISTEN_PORT` | Listen host and port |

Full configuration reference: [docs/configuration.md](./docs/configuration.md).

---

## License

Repository code: MIT (see [LICENSE](./LICENSE))

v0.5+ runtime: 100% MIT (includes custom Go daemon)
