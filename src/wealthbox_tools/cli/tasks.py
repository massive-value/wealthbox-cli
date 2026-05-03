from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import (
    CategoryType,
    TaskCreateInput,
    TaskFrame,
    TaskListQuery,
    TaskPriority,
    TaskType,
    TaskUpdateInput,
)

from ._util import (
    COMMENT_RESOURCE_TYPES,
    OutputFormat,
    build_linked_to,
    build_resource_filter,
    clean_comments,
    handle_errors,
    make_category_command,
    make_resource_app,
    output_result,
    parse_more_fields,
    resolve_category_id,
    run_client,
    run_client_with_comments,
    slim_comments,
    summarize_comments,
)

app = make_resource_app(help="Manage Wealthbox tasks.")
app.command("categories", help="List task category options.")(make_category_command(CategoryType.TASK_CATEGORIES))

_DEFAULT_FIELDS = ["id", "name", "due_date", "frame", "complete", "category"]
_GET_FIELDS = [
    "id", "name", "description", "due_date", "created_at", "complete",
    "priority", "assigned_to", "category", "linked_to",
    "comment_count", "latest_comment",
]
_GET_JSON_FIELDS = [
    "id", "name", "description", "due_date", "created_at", "updated_at",
    "frame", "complete", "repeats", "priority",
    "assigned_to", "assigned_to_team", "creator", "completer",
    "category", "linked_to", "comments",
]

_TASK_CREATE_RESERVED = {
    "name", "due_date", "frame", "priority", "assigned_to", "linked_to", "category", "description",
}


@app.command(
    "list",
    help=(
        "List tasks with optional filters. By default only outstanding tasks are returned; "
        "use --include-completed to include completed tasks"
    ),
)
@handle_errors
def list_tasks(
    contact: int | None = typer.Option(None, "--contact", help="Filter tasks linked to a Contact (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Filter tasks linked to a Project (by ID)"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Filter tasks linked to an Opportunity (by ID)"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Filter by assigned user ID"),
    assigned_to_team: int | None = typer.Option(None, "--assigned-to-team", help="Filter by assigned team ID"),
    created_by: int | None = typer.Option(None, "--created-by", help="Filter by creator user ID"),
    include_completed: bool = typer.Option(
        False, "--include-completed", help="Include completed tasks (default returns outstanding tasks only)"
    ),
    task_type: TaskType | None = typer.Option(None, "--type", help="all, parents, subtasks"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    resource_id, resource_type = build_resource_filter(contact, project, opportunity)

    query = TaskListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        assigned_to=assigned_to,
        assigned_to_team=assigned_to_team,
        created_by=created_by,
        completed=True if include_completed else None,
        task_type=task_type,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    output_result(run_client(token, lambda c: c.list_tasks(query)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("get", help="Get a single task by ID.")
@handle_errors
def get_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    no_comments: bool = typer.Option(False, "--no-comments", help="Omit comments from output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    result = run_client_with_comments(
        token, lambda c: c.get_task(task_id),
        COMMENT_RESOURCE_TYPES["tasks"], task_id, include_comments=not no_comments,
    )
    result = clean_comments(result)
    if not verbose:
        result = {k: result[k] for k in _GET_JSON_FIELDS if k in result}
        result = slim_comments(result)
    if fmt != OutputFormat.JSON:
        result = summarize_comments(result)
        desc = result.get("description", "")
        if isinstance(desc, str) and len(desc) > 50:
            result = {**result, "description": desc[:50] + "..."}
    output_result(result, fmt, fields=None if (verbose or fmt == OutputFormat.JSON) else _GET_FIELDS)


@app.command("add", help="Create a new task. Required: name, and either due_date or frame.")
@handle_errors
def add_task(
    name: str = typer.Argument(..., help="Task title/name"),
    due_date: str | None = typer.Option(
        None, "--due-date", help="Example: '2025-05-24 10:00 AM -0700' (must match Wealthbox format)"
    ),
    frame: TaskFrame | None = typer.Option(None, "--frame", help="Friendly due timeframe"),
    priority: TaskPriority | None = typer.Option(None, "--priority", help="Low, Medium, or High"),
    category: str | None = typer.Option(
        None, "--category",
        help="Task category by name or ID — see: wbox categories task-categories",
    ),
    description: str | None = typer.Option(None, "--description", help="Task description"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Assign to a user by ID"),
    contact: int | None = typer.Option(None, "--contact", help="Link to a Contact by ID"),
    project: int | None = typer.Option(None, "--project", help="Link to a Project by ID"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Link to an Opportunity by ID"),
    more_fields: str | None = typer.Option(
        None, "--more-fields",
        help='JSON: {"complete": false, "assigned_to_team": 456}',
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    # Friendly CLI-level guardrail (still keep model validation too)
    if (due_date is None) == (frame is None):
        raise typer.BadParameter("Provide exactly one --due-date or --frame.")

    payload: dict[str, Any] = {
        "name": name,
        "due_date": due_date,
        "frame": frame,
        "priority": priority,
        "description": description,
        "assigned_to": assigned_to,
        "linked_to": build_linked_to(contact, project, opportunity),
    }

    if more_fields:
        payload.update(parse_more_fields(more_fields, _TASK_CREATE_RESERVED))

    async def _create(client):  # type: ignore[no-untyped-def]
        if category is not None:
            payload["category"] = await resolve_category_id(client, CategoryType.TASK_CATEGORIES, category)
        # Strip None before model construction (due_date XOR frame validator needs clean input)
        clean = {k: v for k, v in payload.items() if v is not None}
        return await client.create_task(TaskCreateInput(**clean))

    output_result(run_client(token, _create), fmt)


@app.command("update", help="Update an existing task. Pass only the fields you want to change.")
@handle_errors
def update_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    name: str | None = typer.Option(None, "--name", help="Task name"),
    due_date: str | None = typer.Option(None, "--due-date", help="ISO 8601 datetime, e.g. '2026-04-01T09:00:00-07:00'"),
    frame: TaskFrame | None = typer.Option(None, "--frame", help="Friendly due timeframe"),
    priority: TaskPriority | None = typer.Option(None, "--priority", help="Low, Medium, or High"),
    category: str | None = typer.Option(
        None, "--category",
        help="Task category by name or ID — see: wbox categories task-categories",
    ),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Reassign to a user by ID"),
    complete: bool | None = typer.Option(None, "--complete/--no-complete", help="Mark as complete or incomplete"),
    description: str | None = typer.Option(None, "--description"),
    contact: int | None = typer.Option(None, "--contact", help="Replace linked Contact (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Replace linked Project (by ID)"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Replace linked Opportunity (by ID)"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {k: v for k, v in {
        "name": name,
        "due_date": due_date,
        "frame": frame,
        "priority": priority,
        "assigned_to": assigned_to,
        "description": description,
    }.items() if v is not None}
    if complete is not None:
        payload["complete"] = complete
    linked = build_linked_to(contact, project, opportunity)
    if linked is not None:
        payload["linked_to"] = linked

    async def _update(client):  # type: ignore[no-untyped-def]
        if category is not None:
            payload["category"] = await resolve_category_id(client, CategoryType.TASK_CATEGORIES, category)
        return await client.update_task(task_id, TaskUpdateInput(**payload))

    output_result(run_client(token, _update), fmt)


@app.command("delete", help="Delete a task by ID.")
@handle_errors
def delete_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    run_client(token, lambda c: c.delete_task(task_id))
    typer.echo(f"Task {task_id} deleted.")
