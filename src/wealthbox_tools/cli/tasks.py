from __future__ import annotations

import asyncio
import json
from typing import Optional

import typer

from wealthbox_tools.models import TaskCreateInput, TaskListQuery, TaskUpdateInput, TaskResourseTypeOptions, TaskTypeOptions

from ._util import get_client, handle_errors, make_category_command, output_result

app = typer.Typer(help="Manage Wealthbox tasks.", no_args_is_help=True)
app.command("categories", help="List task category options.")(make_category_command("task_categories"))


@app.command("list")
@handle_errors
def list_tasks(
    resource_id: Optional[int] = typer.Option(None, "--resource-id", help="Filter by resource id. Must specify resource resource_type"),
    resource_type: TaskResourseTypeOptions = typer.Option(None, "--resource-type", help="Supported Types: Contact, Project, Opportunity"),
    assigned_to: Optional[int] = typer.Option(None, "--assigned-to"),
    assigned_to_team: Optional[int] = typer.Option(None, "--assigned-to-team"),
    created_by: Optional[int] = typer.Option(None, "--created-by", help="user id"),
    completed: Optional[bool] = typer.Option(None, help="Filter by completion status"),
    task_type: TaskTypeOptions = typer.Option(None, "--type", help="all, parents, subtasks"),
    updated_since: Optional[str] = typer.Option(None, "--updated-since"),
    updated_before: Optional[str] = typer.Option(None, "--updated-before"),
    page: Optional[int] = typer.Option(None),
    per_page: Optional[int] = typer.Option(None, "--per-page"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
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
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
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
    data: str = typer.Argument(..., help="JSON object with title and due_date required"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Create a new task. Required fields: title, due_date."""
    input_model = TaskCreateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.create_task(input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("update")
@handle_errors
def update_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    data: str = typer.Argument(..., help="JSON object of fields to update"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
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
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    """Delete a task by ID."""
    async def _run() -> None:
        async with get_client(token) as client:
            await client.delete_task(task_id)

    asyncio.run(_run())
    typer.echo(f"Task {task_id} deleted.")
