"""Top-level Husk CLI built with Typer."""

from __future__ import annotations

import typer

from husk import __version__
from husk.cli import apikey as apikey_cli
from husk.cli import sandbox as sandbox_cli

app = typer.Typer(
    name="husk",
    help="Husk — lightweight AI code sandbox runtime",
    no_args_is_help=True,
    add_completion=False,
)

app.add_typer(sandbox_cli.app, name="sandbox")
app.add_typer(apikey_cli.app, name="apikey")


@app.command()
def version() -> None:
    """Print the Husk version."""
    typer.echo(f"husk {__version__}")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Listen host"),
    port: int = typer.Option(8000, help="Listen port"),
    reload: bool = typer.Option(False, "--reload", help="Hot reload (dev only)"),
) -> None:
    """Start the Husk control plane HTTP server."""
    import uvicorn

    uvicorn.run("husk.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
