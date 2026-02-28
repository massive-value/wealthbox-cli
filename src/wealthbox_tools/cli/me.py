from __future__ import annotations

import asyncio

import typer

from ._util import get_client, handle_errors, output_result

app = typer.Typer(help="Show info about the current authenticated user.")


@app.callback(invoke_without_command=True)
@handle_errors
def get_me(
    ctx: typer.Context,
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Get the current user ("me")."""
    if ctx.invoked_subcommand is not None:
        return
    
    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.get_me()

    output_result(asyncio.run(_run()), fmt)