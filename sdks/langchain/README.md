# langchain-husk

[![PyPI - Version](https://img.shields.io/pypi/v/langchain-husk?label=%20)](https://pypi.org/project/langchain-husk/)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-husk)](https://opensource.org/licenses/MIT)

Husk sandbox integration for [Deep Agents](https://github.com/langchain-ai/deepagents).

## Quick install

```bash
uv add langchain-husk
# or
pip install langchain-husk
```

## Quickstart

```python
from husk_client import Husk

from langchain_husk import HuskSandbox

# Provision the sandbox using husk_client (the SDK).
sandbox = Husk(base_url="http://localhost:8000", api_key="hk_...").create(
    image="python:3.12-slim",
    cpu=2,
    memory_mb=1024,
)

# Wrap it for Deep Agents.
backend = HuskSandbox(sandbox=sandbox, timeout=300)

result = backend.execute("python -c 'print(1+2)'")
print(result.output)        # "3\n"
print(result.exit_code)     # 0

# Use it as a Deep Agents backend:
# from deepagents import DeepAgent
# agent = DeepAgent(backend=backend, ...)

# Always destroy when finished.
sandbox.destroy()
```

The pattern matches `langchain-daytona`: the partner package wraps an
existing SDK sandbox object, it does NOT manage lifecycle. Provisioning
goes through `husk_client.Husk`, destruction through `sandbox.destroy()`.

## What is Husk?

[Husk](https://github.com/husklabs/husk) is a lightweight, MIT-licensed
AI code sandbox runtime — single-process FastAPI control plane + a Go
daemon that runs inside each container. Single `docker run` to start, no
Postgres / Redis / OIDC required.

## License

MIT.
