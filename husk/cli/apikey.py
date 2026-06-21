"""`husk apikey` CLI subcommands."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from husk.auth.service import ApiKeyService
from husk.core import database as db_database
from husk.core.database import init_db

app = typer.Typer(help="Manage API keys (offline; reads/writes the SQLite DB directly)")
console = Console()


@app.command("list")
def list_keys() -> None:
    """List all API keys."""
    asyncio.run(_list())


async def _list() -> None:
    await init_db()
    async with db_database.session_factory() as db:
        keys = await ApiKeyService(db).list()
    if not keys:
        console.print("[dim]no api keys[/dim]")
        return
    t = Table(title="API Keys")
    t.add_column("Name")
    t.add_column("Prefix")
    t.add_column("Created")
    t.add_column("Last Used")
    for k in keys:
        t.add_row(k.name, k.prefix, str(k.created_at), str(k.last_used_at) if k.last_used_at else "-")
    console.print(t)


@app.command()
def create(name: str = typer.Argument(..., help="Friendly name for the key")) -> None:
    """Create a new API key. The plaintext is shown ONCE."""
    plaintext = asyncio.run(_create(name))
    console.print()
    console.print("[bold yellow]Save this — it will NOT be shown again:[/bold yellow]")
    console.print(f"  [bold]{plaintext}[/bold]")
    console.print()


async def _create(name: str) -> str:
    await init_db()
    async with db_database.session_factory() as db:
        _, plaintext = await ApiKeyService(db).create(name)
    return plaintext


@app.command()
def revoke(name: str = typer.Argument(...)) -> None:
    """Revoke an API key by name."""
    asyncio.run(_revoke(name))
    console.print(f"[green]✓[/green] revoked {name}")


async def _revoke(name: str) -> None:
    await init_db()
    async with db_database.session_factory() as db:
        await ApiKeyService(db).revoke(name)
