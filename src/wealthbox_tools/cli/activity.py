from __future__ import annotations

import typer

from wealthbox_tools.models import ActivityListQuery, ActivityType

from ._util import OutputFormat, handle_errors, output_result, run_client, truncate_field

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, help="List Wealthbox activity feed.", no_args_is_help=True)

_BODY_PREVIEW_LEN = 500


@app.command("list", help="List activity feed. Can filter by contact, activity type, and/or updated date range.")
@handle_errors
def list_activity(
    contact: int | None = typer.Option(None, help="Filter by contact ID"),
    cursor: str | None = typer.Option(None, help="Cursor for next page of results"),
    type_: ActivityType | None = typer.Option(None, "--type", help="Activity type filter"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full body content (default truncates to 500 chars)"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = ActivityListQuery(
        contact=contact,
        cursor=cursor,
        type=type_,
        updated_since=updated_since,
        updated_before=updated_before,
    )
    result = run_client(token, lambda c: c.list_activity(query))
    if not verbose:
        result = truncate_field(result, "body", _BODY_PREVIEW_LEN)
    output_result(result, fmt)
