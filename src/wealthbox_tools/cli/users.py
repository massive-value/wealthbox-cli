from __future__ import annotations

import asyncio

import typer

from ._util import get_client, handle_errors, output_result

app = typer.Typer(help="Manage Wealthbox users.", no_args_is_help=True)


@app.command("list")
@handle_errors
def list_users(
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List users."""
    async def _run() -> list[dict]:
        async with get_client(token) as client:
            return await client.list_users()

    output_result(asyncio.run(_run()), fmt)