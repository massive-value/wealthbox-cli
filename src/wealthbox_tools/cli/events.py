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

from ._util import (
    OutputFormat,
    ResourceSpec,
    build_linked_to,
    create_resource_commands,
    handle_errors,
    make_category_command,
    make_resource_app,
    output_result,
    run_client,
)

app = make_resource_app(help="Manage Wealthbox events.")
app.command("categories", help="List event category options.")(make_category_command(CategoryType.EVENT_CATEGORIES))

_DEFAULT_FIELDS = [
    "id", "title", "starts_at", "ends_at", "state", "event_category",
    "comments", "comment_count", "latest_comment",
]


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


@handle_errors
def add_event(
    title: str = typer.Argument(..., help="Event title"),
    starts_at: str = typer.Option(
        ..., "--starts-at", help="Start datetime in ISO 8601, e.g. 2026-01-15T10:00:00-07:00"
    ),
    ends_at: str = typer.Option(
        ..., "--ends-at", help="End datetime in ISO 8601, e.g. 2026-01-15T11:00:00-07:00"
    ),
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


@handle_errors
def update_event(
    event_id: int = typer.Argument(..., help="Event ID"),
    title: str | None = typer.Option(None, "--title", help="Event title"),
    starts_at: str | None = typer.Option(
        None, "--starts-at", help="Start datetime in ISO 8601, e.g. 2026-01-15T10:00:00-07:00"
    ),
    ends_at: str | None = typer.Option(
        None, "--ends-at", help="End datetime in ISO 8601, e.g. 2026-01-15T11:00:00-07:00"
    ),
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


create_resource_commands(
    app,
    ResourceSpec(
        name="events",
        get_func_name="get_event",
        id_arg_name="event_id",
        id_help="Event ID",
        get_client_method="get_event",
        list_help="List events with optional filters.",
        get_help="Get a single event by ID.",
        add_help="Create a new event.",
        update_help="Update an existing event. Pass only the fields you want to change.",
        delete_help="Delete an existing event.",
        get_supports_verbose=True,
        get_default_fields=_DEFAULT_FIELDS,
        list_hook=list_events,
        add_hook=add_event,
        update_hook=update_event,
        delete_client_method="delete_event",
        delete_label="Event",
        operations=frozenset({"list", "get", "add", "update", "delete"}),
    ),
)
