from __future__ import annotations

import asyncio
import json
from typing import Any

import typer

from wealthbox_tools.models import TaskCreateInput, TaskListQuery, TaskUpdateInput, TaskResourceType, TaskType, TaskFrame

from ._util import get_client, handle_errors, make_category_command, output_result

app = typer.Typer(help="Manage Wealthbox tasks.", no_args_is_help=True)
app.command("categories", help="List task category options.")(make_category_command("task_categories"))


@app.command("list")
@handle_errors
def list_tasks(
    resource_id: int | None = typer.Option(None, "--resource-id", help="Filter by resource id. Must specify resource resource_type"),
    resource_type: TaskResourceType | None = typer.Option(None, "--resource-type", help="Supported Types: Contact, Project, Opportunity"),
    assigned_to: int | None = typer.Option(None, "--assigned-to"),
    assigned_to_team: int | None = typer.Option(None, "--assigned-to-team"),
    created_by: int | None = typer.Option(None, "--created-by", help="user id"),
    completed: bool | None = typer.Option(None, help="Filter by completion status"),
    task_type: TaskType | None = typer.Option(None, "--type", help="all, parents, subtasks"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    """List tasks with optional filters."""
    query = TaskListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        assigned_to=assigned_to,
        assigned_to_team=assigned_to_team,
        created_by=created_by,
        completed=completed,
        task_type=task_type,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_tasks(query)

    output_result(asyncio.run(_run()), fmt)


@app.command("get")
@handle_errors
def get_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Get a single task by ID."""
    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.get_task(task_id)

    output_result(asyncio.run(_run()), fmt)


@app.command("create")
@handle_errors
def create_task(
    name: str = typer.Argument(..., help="Task title/name"),
    due_date: str | None = typer.Option(None, "--due-date", help="Example: '2025-05-24 10:00 AM -0700' (must match Wealthbox format)"),
    frame: TaskFrame | None = typer.Option(None, "--frame", help="friendly due timeframe"),
    more_fields: str | None = typer.Option(None, "--more-fields", help='JSON: {"assigned_to": 123456, "linked_to": [{"id": 987654, "type": "Contact"}]}'),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Create a new task. Required: name, and either due_date or frame."""
    # Friendly CLI-level guardrail (still keep model validation too)
    if (due_date is None) == (frame is None):
        raise typer.BadParameter("Provide exactly one --due-date or --frame.")

    payload: dict[str, Any] = {"name": name, "due_date": due_date, "frame": frame}

    if more_fields:
        try:
            extra = json.loads(more_fields)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"--more-fields must be valid JSON: {e.msg}") from e

        if not isinstance(extra, dict):
            raise typer.BadParameter("--more-fields must be a JSON object (e.g. {...}), not a list or string.")

        # Prevent “shadowing” explicit args
        reserved = {"name", "due_date", "frame"}
        collision = reserved.intersection(extra.keys())
        if collision:
            raise typer.BadParameter(f"--more-fields cannot include {sorted(collision)}; use explicit CLI args instead.")

        payload.update(extra)

    # Let Pydantic do the real validation + coercion
    input_model = TaskCreateInput(**payload)

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.create_task(input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("update")
@handle_errors
def update_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    data: str = typer.Argument(..., help="JSON object of fields to update"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Update an existing task."""
    input_model = TaskUpdateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.update_task(task_id, input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("delete")
@handle_errors
def delete_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    """Delete a task by ID."""
    async def _run() -> None:
        async with get_client(token) as client:
            await client.delete_task(task_id)

    asyncio.run(_run())
    typer.echo(f"Task {task_id} deleted.")
