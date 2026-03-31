from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import NoteCreateInput, NoteListQuery, NoteResourceType, NotesOrder, NoteUpdateInput

from ._util import (
    COMMENT_RESOURCE_TYPES,
    OutputFormat,
    build_linked_to,
    handle_errors,
    make_resource_app,
    output_get_result,
    output_result,
    run_client,
    run_client_with_comments,
    truncate_field,
)

app = make_resource_app(help="Manage Wealthbox notes.")

_DEFAULT_FIELDS = [
    "id", "content", "linked_to", "creator_id", "updated_at",
    "comments", "comment_count", "latest_comment",
]
_CONTENT_PREVIEW_LEN = 500


@app.command("list", help="List notes. Can filter by linked resource and/or updated date range.")
@handle_errors
def list_notes(
    contact: int | None = typer.Option(None, "--contact", help="Filter notes linked to a Contact (by ID)"),
    order: NotesOrder | None = typer.Option("updated", help="Sort order: updated or created"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields; content is not truncated"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = NoteListQuery(
        resource_id=contact,
        resource_type=NoteResourceType.CONTACT if contact is not None else None,
        order=order,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    result = run_client(token, lambda c: c.list_notes(query))
    if not verbose:
        result = truncate_field(result, "content", _CONTENT_PREVIEW_LEN)
    output_result(result, fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("get", help="Get a single note by ID.")
@handle_errors
def get_note(
    note_id: int = typer.Argument(..., help="Note ID"),
    no_comments: bool = typer.Option(False, "--no-comments", help="Omit comments from output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    result = run_client_with_comments(
        token, lambda c: c.get_note(note_id),
        COMMENT_RESOURCE_TYPES["notes"], note_id, include_comments=not no_comments,
    )
    output_get_result(result, fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("add", help="Create a new note.")
@handle_errors
def add_note(
    content: str = typer.Argument(..., help="Note body text"),
    contact: int | None = typer.Option(None, "--contact", help="Link to a Contact by ID"),
    project: int | None = typer.Option(None, "--project", help="Link to a Project by ID"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Link to an Opportunity by ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    input_model = NoteCreateInput(
        content=content,
        linked_to=build_linked_to(contact, project, opportunity),
    )
    output_result(run_client(token, lambda c: c.create_note(input_model)), fmt)


@app.command("update", help="Update an existing note. Note: the API does not support deleting notes.")
@handle_errors
def update_note(
    note_id: int = typer.Argument(..., help="Note ID"),
    content: str | None = typer.Option(None, "--content", help="New note body text"),
    contact: int | None = typer.Option(None, "--contact", help="Replace linked Contact (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Replace linked Project (by ID)"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Replace linked Opportunity (by ID)"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {}
    if content is not None:
        payload["content"] = content
    linked = build_linked_to(contact, project, opportunity)
    if linked is not None:
        payload["linked_to"] = linked
    input_model = NoteUpdateInput(**payload)

    output_result(run_client(token, lambda c: c.update_note(note_id, input_model)), fmt)
