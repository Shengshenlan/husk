"""husk-client — Python client for the Husk control plane.

Two layers:

* **Ergonomic** (recommended) — :class:`Husk` and :class:`Sandbox` provide
  a high-level OO API resembling the upstream ``daytona-sdk-python``::

      from husk_client import Husk

      husk = Husk(base_url="http://localhost:8000", api_key="hk_...")
      sandbox = husk.create(image="python:3.12-slim")
      print(sandbox.process.execute("python -c 'print(1+2)'").result)
      sandbox.destroy()

* **Generated** — :class:`AuthenticatedClient` plus the auto-generated
  endpoint-per-function modules in ``husk_client._generated.api.*``.
  Use this when you need an endpoint the ergonomic layer doesn't expose
  yet, or when you want strict type-checking on every field.

To regenerate the auto-generated layer, run from the repo root::

    ./scripts/gen-sdk-clients.sh
"""

from ._generated import AuthenticatedClient, Client
from .ergonomic import (
    DownloadResult,
    ExecuteResult,
    FileInfo,
    Husk,
    Sandbox,
    UploadResult,
)

__version__ = "0.0.1"

__all__ = [
    # ergonomic
    "Husk",
    "Sandbox",
    "ExecuteResult",
    "FileInfo",
    "UploadResult",
    "DownloadResult",
    # generated
    "AuthenticatedClient",
    "Client",
    "__version__",
]
