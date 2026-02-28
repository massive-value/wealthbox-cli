from __future__ import annotations

import asyncio

import typer

from ._util import get_client, handle_errors, output_result

app = typer.Typer(help="List Wealthbox activity feed.", no_args_is_help=True)
from wealthbox_tools.models import ActivityListQuery, ActivityType

@app.command("list")
@handle_errors
def list_activity(
    contact: int | None = typer.Option(None, help="Filter by contact ID"),
    type_: ActivityType | None = typer.Option(None, "--type", help="Activity type filter"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List activity feed."""
    query = ActivityListQuery(
        contact=contact,
        type=type_,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_activity(query)

    output_result(asyncio.run(_run()), fmt)