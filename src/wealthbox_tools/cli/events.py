from __future__ import annotations

import json

import typer

from wealthbox_tools.models import CategoryType, EventCreateInput, EventListQuery, EventUpdateInput, EventsOrder, TaskResourceType

from ._util import handle_errors, make_category_command, output_result, run_client

app = typer.Typer(help="Manage Wealthbox events.", no_args_is_help=True)
app.command("categories", help="List event category options.")(make_category_command(CategoryType.EVENT_CATEGORIES))

_DEFAULT_FIELDS = ["id", "title", "starts_at", "ends_at", "state", "event_category"]


@app.command("list", help="List events with optional filters.")
@handle_errors
def list_events(
    resource_id: int | None = typer.Option(None, "--resource-id", help="Filter by resource ID"),
    resource_type: TaskResourceType | None = typer.Option(None, "--resource-type", help="Supports: Contact, Project, Opportunity"),
    start_date_min: str | None = typer.Option(None, "--start-date-min", help="Format example: '2015-05-24 10:00 AM -0400'"),
    start_date_max: str | None = typer.Option(None, "--start-date-max", help="Format example: '2015-05-24 10:00 AM -0400'"),
    order: EventsOrder | None = typer.Option(None, "--order", help="asc, desc, recent, created"),
    updated_since: str | None = typer.Option(None, "--updated-since", help="Format example: '2015-05-24 10:00 AM -0400'"),
    updated_before: str | None = typer.Option(None, "--updated-before", help="Format example: '2015-05-24 10:00 AM -0400'"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    query = EventListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        start_date_min=start_date_min,
        start_date_max=start_date_max,
        order=order,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    output_result(run_client(token, lambda c: c.list_events(query)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("get", help="Get a single event by ID.")
@handle_errors
def get_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.get_event(event_id)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("create", help="Create a new event. Required fields: title, starts_at.")
@handle_errors
def create_event(
    data: str = typer.Argument(..., help="JSON object with title and starts_at required"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    input_model = EventCreateInput(**json.loads(data))

    output_result(run_client(token, lambda c: c.create_event(input_model)), fmt)


@app.command("update", help="Update an existing event.")
@handle_errors
def update_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    data: str = typer.Argument(..., help="JSON object of fields to update"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    input_model = EventUpdateInput(**json.loads(data))

    output_result(run_client(token, lambda c: c.update_event(event_id, input_model)), fmt)


@app.command("delete", help="Delete an existing event.")
@handle_errors
def delete_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    run_client(token, lambda c: c.delete_event(event_id))
    typer.echo(f"Event {event_id} deleted.")
