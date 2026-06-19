"""`husk sandbox` CLI subcommands."""

from __future__ import annotations

import asyncio
import json

import httpx
import typer
from rich.console import Console
from rich.table import Table

from husk.core.config import settings

app = typer.Typer(help="Manage sandboxes")
console = Console()


def _client() -> httpx.Client:
    api_key = _get_api_key()
    return httpx.Client(
        base_url=f"http://{settings.listen_host}:{settings.listen_port}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60.0,
    )


def _get_api_key() -> str:
    """Read API key: env var > settings > error."""
    key = settings.root_api_key
    if not key:
        raise typer.BadParameter("No HUSK_ROOT_API_KEY set. Run with the env var.")
    return key


@app.command("list")
def list_sandboxes() -> None:
    """List all sandboxes."""
    with _client() as c:
        r = c.get("/api/sandbox")
    r.raise_for_status()
    rows = r.json()

    if not rows:
        console.print("[dim]no sandboxes[/dim]")
        return

    t = Table(title="Sandboxes")
    t.add_column("ID")
    t.add_column("Name")
    t.add_column("State")
    t.add_column("Image")
    t.add_column("CPU/Mem")
    for sb in rows:
        t.add_row(
            sb["id"],
            sb["name"],
            f"[green]{sb['state']}[/green]" if sb["state"] == "started" else sb["state"],
            sb.get("snapshot_id") or "-",
            f"{sb['cpu']}c/{sb['memory_mb']}m",
        )
    console.print(t)


@app.command("new")
def create_sandbox(
    name: str | None = typer.Option(None, help="Sandbox name (auto-generated if omitted)"),
    image: str = typer.Option("alpine:3.20", "--image", "-i"),
    cpu: int = typer.Option(1, help="CPU cores"),
    memory: int = typer.Option(512, help="Memory in MB"),
) -> None:
    """Create a new sandbox."""
    payload = {"snapshot_id": image, "cpu": cpu, "memory_mb": memory}
    if name:
        payload["name"] = name
    with _client() as c:
        r = c.post("/api/sandbox", json=payload)
    if r.status_code >= 400:
        console.print(f"[red]{r.status_code}[/red] {r.text}")
        raise typer.Exit(1)
    sb = r.json()
    console.print(f"[green]✓[/green] {sb['id']}  {sb['name']}  state={sb['state']}")


@app.command("get")
def get_sandbox(sandbox_id: str) -> None:
    """Show sandbox details."""
    with _client() as c:
        r = c.get(f"/api/sandbox/{sandbox_id}")
    if r.status_code >= 400:
        console.print(f"[red]{r.status_code}[/red] {r.text}")
        raise typer.Exit(1)
    console.print_json(json.dumps(r.json()))


@app.command()
def start(sandbox_id: str) -> None:
    """Start a stopped sandbox."""
    _action(sandbox_id, "start")


@app.command()
def stop(sandbox_id: str) -> None:
    """Stop a running sandbox."""
    _action(sandbox_id, "stop")


@app.command("rm")
def delete(sandbox_id: str) -> None:
    """Destroy a sandbox."""
    with _client() as c:
        r = c.delete(f"/api/sandbox/{sandbox_id}")
    if r.status_code >= 400:
        console.print(f"[red]{r.status_code}[/red] {r.text}")
        raise typer.Exit(1)
    console.print(f"[green]✓[/green] destroyed {sandbox_id}")


def _action(sandbox_id: str, verb: str) -> None:
    with _client() as c:
        r = c.post(f"/api/sandbox/{sandbox_id}/{verb}")
    if r.status_code >= 400:
        console.print(f"[red]{r.status_code}[/red] {r.text}")
        raise typer.Exit(1)
    sb = r.json()
    console.print(f"[green]✓[/green] {sb['id']} state={sb['state']}")


# Async stub for future hot-loops; kept for symmetry with other CLI modules.
async def _noop() -> None:  # pragma: no cover
    await asyncio.sleep(0)
