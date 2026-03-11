from __future__ import annotations

import json
from typing import Any

import typer

from wealthbox_tools.models import CategoryType, TaskCreateInput, TaskListQuery, TaskUpdateInput, TaskResourceType, TaskType, TaskFrame, TaskPriority

from ._util import build_linked_to, handle_errors, make_category_command, output_result, run_client

app = typer.Typer(help="Manage Wealthbox tasks.", no_args_is_help=True)
app.command("categories", help="List task category options.")(make_category_command(CategoryType.TASK_CATEGORIES))

_DEFAULT_FIELDS = ["id", "name", "due_date", "frame", "complete", "category"]


@app.command("list", help="Returns a list of tasks, with optional filters. By default, only outstanding tasks are returned; use --include-completed to include completed tasks in the results.")
@handle_errors
def list_tasks(
    resource_id: int | None = typer.Option(None, "--resource-id", help="Filter by resource id. Must specify resource resource_type"),
    resource_type: TaskResourceType | None = typer.Option(None, "--resource-type", help="Supported Types: Contact, Project, Opportunity"),
    assigned_to: int | None = typer.Option(None, "--assigned-to"),
    assigned_to_team: int | None = typer.Option(None, "--assigned-to-team"),
    created_by: int | None = typer.Option(None, "--created-by", help="user id"),
    include_completed: bool = typer.Option(False, "--include-completed", help="Include completed tasks (default returns outstanding tasks only)"),
    task_type: TaskType | None = typer.Option(None, "--type", help="all, parents, subtasks"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.get_task(task_id)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("add", help="Create a new task. Required: name, and either due_date or frame.")
@handle_errors
def add_task(
    name: str = typer.Argument(..., help="Task title/name"),
    due_date: str | None = typer.Option(None, "--due-date", help="Example: '2025-05-24 10:00 AM -0700' (must match Wealthbox format)"),
    frame: TaskFrame | None = typer.Option(None, "--frame", help="friendly due timeframe"),
    priority: TaskPriority | None = typer.Option(None, "--priority", help="Low, Medium, or High"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Assign to a user by ID"),
    contact: int | None = typer.Option(None, "--contact", help="Link to a Contact by ID"),
    project: int | None = typer.Option(None, "--project", help="Link to a Project by ID"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Link to an Opportunity by ID"),
    more_fields: str | None = typer.Option(None, "--more-fields", help='JSON: {"category": 123, "complete": false, "assigned_to_team": 456, "description": "..."}'),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    # Friendly CLI-level guardrail (still keep model validation too)
    if (due_date is None) == (frame is None):
        raise typer.BadParameter("Provide exactly one --due-date or --frame.")

    payload: dict[str, Any] = {
        "name": name,
        "due_date": due_date,
        "frame": frame,
        "priority": priority,
        "assigned_to": assigned_to,
        "linked_to": build_linked_to(contact, project, opportunity),
    }

    if more_fields:
        try:
            extra = json.loads(more_fields)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--more-fields must be valid JSON: {e.msg}") from e

        if not isinstance(extra, dict):
            raise typer.BadParameter("--more-fields must be a JSON object (e.g. {...}), not a list or string.")

        # Prevent "shadowing" explicit args
        reserved = {"name", "due_date", "frame", "priority", "assigned_to", "linked_to"}
        collision = reserved.intersection(extra.keys())
        if collision:
            raise typer.BadParameter(f"--more-fields cannot include {sorted(collision)}; use explicit CLI args instead.")

        payload.update(extra)

    # Strip None before model construction (due_date XOR frame validator needs clean input)
    input_model = TaskCreateInput(**{k: v for k, v in payload.items() if v is not None})

    output_result(run_client(token, lambda c: c.create_task(input_model)), fmt)


@app.command("update", help="Update an existing task. Pass only the fields you want to change.")
@handle_errors
def update_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    name: str | None = typer.Option(None, "--name", help="Task name"),
    due_date: str | None = typer.Option(None, "--due-date", help="Example: '2025-05-24 10:00 AM -0700'"),
    frame: TaskFrame | None = typer.Option(None, "--frame", help="Friendly due timeframe"),
    priority: TaskPriority | None = typer.Option(None, "--priority", help="Low, Medium, or High"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Reassign to a user by ID"),
    complete: bool | None = typer.Option(None, "--complete/--no-complete", help="Mark as complete or incomplete"),
    description: str | None = typer.Option(None, "--description"),
    contact: int | None = typer.Option(None, "--contact", help="Replace linked Contact (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Replace linked Project (by ID)"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Replace linked Opportunity (by ID)"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
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
    input_model = TaskUpdateInput(**payload)

    output_result(run_client(token, lambda c: c.update_task(task_id, input_model)), fmt)


@app.command("delete", help="Delete a task by ID.")
@handle_errors
def delete_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    run_client(token, lambda c: c.delete_task(task_id))
    typer.echo(f"Task {task_id} deleted.")
