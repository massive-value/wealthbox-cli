from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import CommentListQuery, CommentResourceType

from ._util import (
    OutputFormat,
    _strip_html,
    clean_comments,
    handle_errors,
    output_result,
    run_client,
    truncate_field,
)

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help=(
        "Read comments on work records. Comments are also included inline by "
        "`wbox tasks/events/notes/opportunities/projects/workflows get`."
    ),
    no_args_is_help=True,
)

_DEFAULT_FIELDS = ["id", "resource_type", "resource_id", "creator", "created_at", "text"]

# Comment bodies arrive as {"text": ..., "html": ...} where "text" is itself
# HTML. Left alone they blow out a table row and bury the message, so default
# output unnests and strips them; tabular output also trims to a preview.
_TEXT_PREVIEW_LEN = 120


def _slim(comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reduce each comment to the default fields, with body flattened to plain text."""
    slimmed = []
    for c in comments:
        entry: dict[str, Any] = {k: c.get(k) for k in _DEFAULT_FIELDS if k != "text"}
        body = c.get("body")
        raw = body.get("text", "") if isinstance(body, dict) else str(body or "")
        entry["text"] = _strip_html(raw)
        slimmed.append(entry)
    return slimmed

# CLI flag -> the resource_type string GET /comments expects. Notes are
# "StatusUpdates" on the wire; Contacts are absent because /comments rejects
# them (see the note in CLAUDE.md on `wbox contacts get`).
_RESOURCE_FLAGS: dict[str, CommentResourceType] = {
    "task": CommentResourceType.TASK,
    "event": CommentResourceType.EVENT,
    "note": CommentResourceType.STATUS_UPDATES,
    "opportunity": CommentResourceType.OPPORTUNITY,
    "project": CommentResourceType.PROJECT,
    "workflow": CommentResourceType.WORKFLOW,
}


def _pick_resource(**flags: int | None) -> tuple[int, CommentResourceType] | None:
    """Return the single (id, type) the caller asked for, or None if they asked for none."""
    chosen = [(name, value) for name, value in flags.items() if value is not None]
    if not chosen:
        return None
    if len(chosen) > 1:
        names = ", ".join(f"--{n}" for n, _ in sorted(chosen))
        raise typer.BadParameter(f"Provide only one resource filter; got {names}.")
    name, value = chosen[0]
    return value, _RESOURCE_FLAGS[name]


@app.command(
    "list",
    help=(
        "List comments for one record, or for a time window. "
        "Requires a resource filter or --updated-since/--updated-before."
    ),
)
@handle_errors
def list_comments(
    task: int | None = typer.Option(None, "--task", help="Comments on a Task (by ID)"),
    event: int | None = typer.Option(None, "--event", help="Comments on an Event (by ID)"),
    note: int | None = typer.Option(None, "--note", help="Comments on a Note (by ID)"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Comments on an Opportunity (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Comments on a Project (by ID)"),
    workflow: int | None = typer.Option(None, "--workflow", help="Comments on a Workflow (by ID)"),
    updated_since: str | None = typer.Option(None, "--updated-since", help="ISO 8601 datetime"),
    updated_before: str | None = typer.Option(None, "--updated-before", help="ISO 8601 datetime"),
    page: int | None = typer.Option(None, help="Page number"),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    resource = _pick_resource(
        task=task, event=event, note=note,
        opportunity=opportunity, project=project, workflow=workflow,
    )
    # An unfiltered walk scans every comment in the workspace: roughly 8.5s per
    # page of 100, versus ~1.5s per page inside a one-month window. Refusing is
    # cheaper than letting an agent discover that by waiting.
    if resource is None and updated_since is None and updated_before is None:
        raise ValueError(
            "Refusing an unfiltered comment query: GET /comments costs about 8.5s per page of "
            "100 without a filter (about 1.5s with one). Pass a resource filter "
            "(--task/--event/--note/--opportunity/--project/--workflow) or a window "
            "(--updated-since/--updated-before)."
        )

    resource_id, resource_type = resource if resource else (None, None)
    query = CommentListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )
    result = run_client(token, lambda c: c.list_comments(query))
    if verbose:
        result = clean_comments(result)
    else:
        result = {**result, "comments": _slim(result.get("comments", []))}
        if fmt != OutputFormat.JSON:
            result = truncate_field(result, "text", _TEXT_PREVIEW_LEN)
    output_result(result, fmt, fields=None if verbose else _DEFAULT_FIELDS)
