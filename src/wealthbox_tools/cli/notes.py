from __future__ import annotations

import asyncio
import json

import typer

from wealthbox_tools.models import NoteCreateInput, NoteListQuery, NoteUpdateInput
from wealthbox_tools.models import NotesOrder

from ._util import get_client, handle_errors, output_result

app = typer.Typer(help="Manage Wealthbox notes.", no_args_is_help=True)


@app.command("list")
@handle_errors
def list_notes(
    resource_id: int | None = typer.Option(None),
    resource_type: str | None = typer.Option(None),
    order: NotesOrder | None = typer.Option("updated"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List notes."""
    query = NoteListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        order=order,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_notes(query)

    output_result(asyncio.run(_run()), fmt)


@app.command("get")
@handle_errors
def get_note(
    note_id: int = typer.Argument(..., help="Note ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Get a single note by ID."""
    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.get_note(note_id)

    output_result(asyncio.run(_run()), fmt)


@app.command("create")
@handle_errors
def create_note(
    data: str = typer.Argument(..., help="JSON object with content required. Optionally linked_to: [{id, type}]."),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Create a new note. Required: content."""
    input_model = NoteCreateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.create_note(input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("update")
@handle_errors
def update_note(
    note_id: int = typer.Argument(..., help="Note ID"),
    data: str = typer.Argument(..., help="JSON object of fields to update"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Update an existing note. Note: the API does not support deleting notes."""
    input_model = NoteUpdateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.update_note(note_id, input_model)

    output_result(asyncio.run(_run()), fmt)
