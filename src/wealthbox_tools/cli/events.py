from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import (
    CategoryType,
    EventCreateInput,
    EventListQuery,
    EventsOrder,
    EventsState,
    EventUpdateInput,
    TaskResourceType,
)

from ._util import OutputFormat, build_linked_to, handle_errors, make_category_command, output_result, run_client

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Manage Wealthbox events.",
    no_args_is_help=True,
)
app.command("categories", help="List event category options.")(make_category_command(CategoryType.EVENT_CATEGORIES))

_DEFAULT_FIELDS = ["id", "title", "starts_at", "ends_at", "state", "event_category"]


@app.command("list", help="List events with optional filters.")
@handle_errors
def list_events(
    resource_id: int | None = typer.Option(None, "--resource-id", help="Filter by resource ID"),
    resource_type: TaskResourceType | None = typer.Option(
        None, "--resource-type", help="Supports: Contact, Project, Opportunity"
    ),
    start_date_min: str | None = typer.Option(
        None, "--start-date-min", help="Format example: '2015-05-24 10:00 AM -0400'"
    ),
    start_date_max: str | None = typer.Option(
        None, "--start-date-max", help="Format example: '2015-05-24 10:00 AM -0400'"
    ),
    order: EventsOrder | None = typer.Option(None, "--order", help="Sort order: asc, desc, recent, created"),
    updated_since: str | None = typer.Option(
        None, "--updated-since", help="Format example: '2015-05-24 10:00 AM -0400'"
    ),
    updated_before: str | None = typer.Option(
        None, "--updated-before", help="Format example: '2015-05-24 10:00 AM -0400'"
    ),
    page: int | None = typer.Option(None, help="Page number"),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
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
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.get_event(event_id)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("add", help="Create a new event.")
@handle_errors
def add_event(
    title: str = typer.Argument(..., help="Event title"),
    starts_at: str = typer.Option(..., "--starts-at", help="Start datetime in ISO 8601, e.g. '2026-01-15T10:00:00-07:00'"),
    ends_at: str = typer.Option(..., "--ends-at", help="End datetime in ISO 8601, e.g. '2026-01-15T11:00:00-07:00'"),
    location: str | None = typer.Option(None, "--location"),
    state: EventsState | None = typer.Option(
        None, "--state", help="unconfirmed, confirmed, tentative, completed, cancelled"
    ),
    all_day: bool | None = typer.Option(None, "--all-day/--no-all-day"),
    description: str | None = typer.Option(None, "--description"),
    event_category: int | None = typer.Option(None, "--category", help="Event category ID"),
    contact: int | None = typer.Option(None, "--contact", help="Link to a Contact by ID"),
    project: int | None = typer.Option(None, "--project", help="Link to a Project by ID"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Link to an Opportunity by ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    input_model = EventCreateInput(
        title=title,
        starts_at=starts_at,
        ends_at=ends_at,
        location=location,
        state=state,
        all_day=all_day,
        description=description,
        event_category=event_category,
        linked_to=build_linked_to(contact, project, opportunity),
    )
    output_result(run_client(token, lambda c: c.create_event(input_model)), fmt)


@app.command("update", help="Update an existing event. Pass only the fields you want to change.")
@handle_errors
def update_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    title: str | None = typer.Option(None, "--title", help="Event title"),
    starts_at: str | None = typer.Option(None, "--starts-at", help="Start datetime in ISO 8601, e.g. '2026-01-15T10:00:00-07:00'"),
    ends_at: str | None = typer.Option(None, "--ends-at", help="End datetime in ISO 8601, e.g. '2026-01-15T11:00:00-07:00'"),
    location: str | None = typer.Option(None, "--location"),
    state: EventsState | None = typer.Option(
        None, "--state", help="unconfirmed, confirmed, tentative, completed, cancelled"
    ),
    all_day: bool | None = typer.Option(None, "--all-day/--no-all-day"),
    description: str | None = typer.Option(None, "--description"),
    event_category: int | None = typer.Option(None, "--category", help="Event category ID"),
    contact: int | None = typer.Option(None, "--contact", help="Replace linked Contact (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Replace linked Project (by ID)"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Replace linked Opportunity (by ID)"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {k: v for k, v in {
        "title": title,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "location": location,
        "state": state,
        "description": description,
        "event_category": event_category,
    }.items() if v is not None}
    if all_day is not None:
        payload["all_day"] = all_day
    linked = build_linked_to(contact, project, opportunity)
    if linked is not None:
        payload["linked_to"] = linked
    input_model = EventUpdateInput(**payload)

    output_result(run_client(token, lambda c: c.update_event(event_id, input_model)), fmt)


@app.command("delete", help="Delete an existing event.")
@handle_errors
def delete_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    run_client(token, lambda c: c.delete_event(event_id))
    typer.echo(f"Event {event_id} deleted.")
