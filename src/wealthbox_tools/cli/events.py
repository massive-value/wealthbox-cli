from __future__ import annotations

import asyncio
import json
from typing import Optional

import typer

from wealthbox_tools.models import EventCreateInput, EventListQuery, EventUpdateInput, EventsOrderOptions

from ._util import get_client, handle_errors, make_category_command, output_result

app = typer.Typer(help="Manage Wealthbox events.", no_args_is_help=True)
app.command("categories", help="List event category options.")(make_category_command("event_categories"))


@app.command("list")
@handle_errors
def list_events(
    resource_id: Optional[int] = typer.Option(None, "--resource-id", help="Filter by resource ID"),
    resource_type: Optional[str] = typer.Option(None, "--resource-type"),
    start_date_min: Optional[str] = typer.Option(None, "--start-date-min", help="ISO datetime"),
    start_date_max: Optional[str] = typer.Option(None, "--start-date-max", help="ISO datetime"),
    order: Optional[EventsOrderOptions] = typer.Option(None, "--order", help="asc, desc, recent, created"),
    page: Optional[int] = typer.Option(None),
    per_page: Optional[int] = typer.Option(None, "--per-page"),
    updated_since: Optional[str] = typer.Option(None, "--updated-since"),
    updated_before: Optional[str] = typer.Option(None, "--updated-before"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List events with optional filters."""
    query = EventListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        start_date_min=start_date_min,
        start_date_max=start_date_max,
        order=order,
        page=page,
        per_page=per_page,
        updated_since=updated_since,
        updated_before=updated_before,
    )

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_events(query)

    output_result(asyncio.run(_run()), fmt)


@app.command("get")
@handle_errors
def get_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Get a single event by ID."""
    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.get_event(event_id)

    output_result(asyncio.run(_run()), fmt)


@app.command("create")
@handle_errors
def create_event(
    data: str = typer.Argument(..., help="JSON object with title and starts_at required"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Create a new event. Required fields: title, starts_at."""
    input_model = EventCreateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.create_event(input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("update")
@handle_errors
def update_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    data: str = typer.Argument(..., help="JSON object of fields to update"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Update an existing event."""
    input_model = EventUpdateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.update_event(event_id, input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("delete")
@handle_errors
def delete_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    """Delete an event by ID."""
    async def _run() -> None:
        async with get_client(token) as client:
            await client.delete_event(event_id)

    asyncio.run(_run())
    typer.echo(f"Event {event_id} deleted.")
