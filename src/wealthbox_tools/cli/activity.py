from __future__ import annotations

import typer

from wealthbox_tools.models import ActivityListQuery, ActivityType

from ._util import handle_errors, output_result, run_client

app = typer.Typer(help="List Wealthbox activity feed.", no_args_is_help=True)


@app.command("list")
@handle_errors
def list_activity(
    contact: int | None = typer.Option(None, help="Filter by contact ID"),
    cursor: str | None = typer.Option(None, help="Cursor for next page of results"),
    type_: ActivityType | None = typer.Option(None, "--type", help="Activity type filter"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List activity feed."""
    query = ActivityListQuery(
        contact=contact,
        cursor=cursor,
        type=type_,
        updated_since=updated_since,
        updated_before=updated_before,
    )
    output_result(run_client(token, lambda c: c.list_activity(query)), fmt)
