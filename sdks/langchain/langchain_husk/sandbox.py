"""Husk sandbox backend implementation for Deep Agents.

This module is intentionally minimal: it adapts an existing
``husk_client.Sandbox`` to the Deep Agents
:class:`deepagents.backends.protocol.SandboxBackendProtocol`. Sandbox
provisioning and destruction are handled by ``husk_client.Husk`` —
``langchain_husk`` does not duplicate that responsibility.

This mirrors the ``langchain-daytona`` shape: the partner package wraps
an SDK object, it does NOT subsume the SDK's lifecycle helpers.
"""

from __future__ import annotations

import husk_client
from deepagents.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from deepagents.backends.sandbox import BaseSandbox

_DEFAULT_TIMEOUT = 30 * 60  # 30 minutes


class HuskSandbox(BaseSandbox):
    """Husk sandbox implementation conforming to ``SandboxBackendProtocol``.

    Wraps a :class:`husk_client.Sandbox` (which the caller is responsible
    for creating and eventually destroying via ``husk_client.Husk``).

    All file operations are inherited from
    :class:`deepagents.backends.sandbox.BaseSandbox`, which composes them
    out of :meth:`execute` and :meth:`upload_files`. We override
    :meth:`download_files` directly because the Husk daemon has a native
    download endpoint and going through ``execute`` would add a base64
    round-trip.

    Example::

        from husk_client import Husk
        from langchain_husk import HuskSandbox

        sandbox = Husk(base_url=..., api_key=...).create(image="python:3.12-slim")
        backend = HuskSandbox(sandbox=sandbox)
        result = backend.execute("python -c 'print(1+2)'")
        print(result.output)
        sandbox.destroy()
    """

    def __init__(
        self,
        *,
        sandbox: husk_client.Sandbox,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        """Wrap an existing Husk sandbox.

        Args:
            sandbox: A live :class:`husk_client.Sandbox` instance, typically
                obtained from :meth:`husk_client.Husk.create` or
                :meth:`husk_client.Husk.get`.
            timeout: Default per-command timeout in seconds, used when
                :meth:`execute` is called without an explicit ``timeout``.
                Husk treats ``0`` as "wait indefinitely".
        """
        self._sandbox = sandbox
        self._default_timeout = timeout

    # ── identity ──

    @property
    def id(self) -> str:
        """Return the underlying Husk sandbox id (``sb_...``)."""
        return self._sandbox.id

    # ── execute ──

    def execute(
        self,
        command: str,
        *,
        timeout: int | None = None,
    ) -> ExecuteResponse:
        """Execute a shell command inside the sandbox.

        Args:
            command: Shell command string to execute (run as ``sh -c <cmd>``).
            timeout: Maximum time in seconds to wait for the command. If
                None, uses the backend's default. Husk treats ``0`` as
                "wait indefinitely".
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout
        try:
            result = self._sandbox.process.execute(command, timeout=effective_timeout)
        except TimeoutError:
            return ExecuteResponse(
                output=f"Command timed out after {effective_timeout} seconds",
                exit_code=124,
                truncated=False,
            )
        except Exception as e:  # noqa: BLE001 — surface as exec failure
            return ExecuteResponse(
                output=f"<husk error>{type(e).__name__}: {e}</husk error>",
                exit_code=1,
                truncated=False,
            )

        output = result.stdout
        if result.stderr.strip():
            output = f"{output}\n<stderr>{result.stderr.strip()}</stderr>"
        return ExecuteResponse(
            output=output,
            exit_code=result.exit_code,
            truncated=False,
        )

    # ── files ──

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload files into the sandbox.

        Delegates to :meth:`husk_client.Sandbox.fs.upload_files`, which
        already returns per-file outcomes. Non-absolute paths are surfaced
        as ``error="invalid_path"``.
        """
        results = self._sandbox.fs.upload_files(files)
        return [
            FileUploadResponse(path=r.path, error=r.error)
            for r in results
        ]

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download files from the sandbox.

        Delegates to :meth:`husk_client.Sandbox.fs.download_files`. Missing
        files yield ``error="file_not_found"``; non-absolute paths yield
        ``error="invalid_path"``.
        """
        results = self._sandbox.fs.download_files(paths)
        return [
            FileDownloadResponse(path=r.path, content=r.content, error=r.error)
            for r in results
        ]
