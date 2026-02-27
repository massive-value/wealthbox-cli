from __future__ import annotations

import asyncio
import json
from typing import Optional

import typer

from wealthbox_tools.models import TaskCreateInput, TaskListQuery, TaskUpdateInput

from ._util import get_client, handle_errors, make_category_command, output_result

app = typer.Typer(help="Manage Wealthbox tasks.", no_args_is_help=True)
app.command("categories", help="List task category options.")(make_category_command("task_categories"))


@app.command("list")
@handle_errors
def list_tasks(
    title: Optional[str] = typer.Option(None, help="Filter by title"),
    assigned_to_user_id: Optional[int] = typer.Option(None, "--assigned-to-user-id"),
    assigned_to_team_id: Optional[int] = typer.Option(None, "--assigned-to-team-id"),
    category_id: Optional[int] = typer.Option(None, "--category-id"),
    completed: Optional[bool] = typer.Option(None, help="Filter by completion status"),
    due_date: Optional[str] = typer.Option(None, "--due-date"),
    page: Optional[int] = typer.Option(None),
    per_page: Optional[int] = typer.Option(None, "--per-page"),
    updated_since: Optional[str] = typer.Option(None, "--updated-since"),
    updated_before: Optional[str] = typer.Option(None, "--updated-before"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
) -> None:
    """List tasks with optional filters."""
    query = TaskListQuery(
        title=title,
        assigned_to_user_id=assigned_to_user_id,
        assigned_to_team_id=assigned_to_team_id,
        category_id=category_id,
        completed=completed,
        due_date=due_date,
        page=page,
        per_page=per_page,
        updated_since=updated_since,
        updated_before=updated_before,
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
