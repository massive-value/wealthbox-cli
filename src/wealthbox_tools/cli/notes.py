from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import NoteCreateInput, NoteListQuery, NoteUpdateInput
from wealthbox_tools.models import NotesOrder

from ._util import build_linked_to, handle_errors, output_result, run_client

app = typer.Typer(help="Manage Wealthbox notes.", no_args_is_help=True)

_DEFAULT_FIELDS = ["id", "content", "linked_to", "creator_id", "updated_at"]


@app.command("list", help="List notes. Can filter by linked resource and/or updated date range.")
@handle_errors
def list_notes(
    resource_id: int | None = typer.Option(None),
    resource_type: str | None = typer.Option(None),
    order: NotesOrder | None = typer.Option("updated"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    query = NoteListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        order=order,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    output_result(run_client(token, lambda c: c.list_notes(query)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("get", help="Get a single note by ID.")
@handle_errors
def get_note(
    note_id: int = typer.Argument(..., help="Note ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.get_note(note_id)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("add", help="Create a new note.")
@handle_errors
def add_note(
    content: str = typer.Argument(..., help="Note body text"),
    contact: int | None = typer.Option(None, "--contact", help="Link to a Contact by ID"),
    project: int | None = typer.Option(None, "--project", help="Link to a Project by ID"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Link to an Opportunity by ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
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
    fmt: str = typer.Option("json", "--format"),
) -> None:
    payload: dict[str, Any] = {}
    if content is not None:
        payload["content"] = content
    linked = build_linked_to(contact, project, opportunity)
    if linked is not None:
        payload["linked_to"] = linked
    input_model = NoteUpdateInput(**payload)

    output_result(run_client(token, lambda c: c.update_note(note_id, input_model)), fmt)
