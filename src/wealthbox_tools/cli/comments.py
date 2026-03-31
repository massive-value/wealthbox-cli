from __future__ import annotations

import typer

from wealthbox_tools.models import CommentListQuery, CommentResourceType

from ._util import OutputFormat, handle_errors, output_result, run_client, truncate_nested_field

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Retrieve Wealthbox comments.",
    no_args_is_help=True,
)

_DEFAULT_FIELDS = ["id", "creator", "resource_type", "resource_id", "created_at", "updated_at", "body"]
_BODY_PREVIEW_LEN = 500


@app.command("list", help="List comments. Filter by resource ID/type and/or updated date range.")
@handle_errors
def list_comments(
    resource_id: int | None = typer.Option(
        None, "--resource-id", help="Filter by resource ID (requires --resource-type)"
    ),
    resource_type: CommentResourceType | None = typer.Option(
        None, "--resource-type", help="Filter by resource type: Contact, Task, Event"
    ),
    updated_since: str | None = typer.Option(
        None, "--updated-since", help="Only comments updated on or after this timestamp"
    ),
    updated_before: str | None = typer.Option(
        None, "--updated-before", help="Only comments updated on or before this timestamp"
    ),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = CommentListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )
    result = run_client(token, lambda c: c.list_comments(query))
    if not verbose:
        result = truncate_nested_field(result, "body", ["text", "html"], _BODY_PREVIEW_LEN)
    output_result(result, fmt, fields=None if verbose else _DEFAULT_FIELDS)
