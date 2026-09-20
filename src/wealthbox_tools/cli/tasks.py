from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.client import WealthboxClient
from wealthbox_tools.models import (
    CategoryType,
    DocumentType,
    TaskCreateInput,
    TaskFrame,
    TaskListQuery,
    TaskPriority,
    TaskStatusFilter,
    TaskType,
    TaskUpdateInput,
)

from ._util import (
    COMMENT_RESOURCE_TYPES,
    OutputFormat,
    ResourceSpec,
    build_linked_to,
    build_resource_filter,
    clean_comments,
    create_resource_commands,
    handle_errors,
    make_category_command,
    make_resource_app,
    output_result,
    parse_more_fields,
    resolve_category_id,
    resolve_custom_fields,
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


def _normalize_frame(value: str | None) -> TaskFrame | None:
    """Accept both kebab-case and snake_case for --frame; return a TaskFrame.

    The CLI uses kebab-case for every other multi-word value (--contact-type,
    --assigned-to, etc.), so users naturally try `--frame next-week`. The API
    requires snake_case (``next_week``); we normalize before validating.
    """
    if value is None:
        return None
    normalized = value.replace("-", "_").lower()
    try:
        return TaskFrame(normalized)
    except ValueError as exc:
        choices = ", ".join(repr(m.value) for m in TaskFrame)
        raise typer.BadParameter(
            f"{value!r} is not one of {choices}.",
            param_hint="'--frame'",
        ) from exc


_FRAME_HELP = (
    "Friendly due timeframe. One of: today, tomorrow, this-week / this_week, "
    "next-week / next_week, future, specific."
)


@handle_errors
def list_tasks(
    contact: int | None = typer.Option(None, "--contact", help="Filter tasks linked to a Contact (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Filter tasks linked to a Project (by ID)"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Filter tasks linked to an Opportunity (by ID)"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Filter by assigned user ID"),
    assigned_to_team: int | None = typer.Option(None, "--assigned-to-team", help="Filter by assigned team ID"),
    created_by: int | None = typer.Option(None, "--created-by", help="Filter by creator user ID"),
    status: TaskStatusFilter = typer.Option(
        TaskStatusFilter.OPEN, "--status",
        help=(
            "Which tasks to return: open (Wealthbox's own default), completed, or all. "
            "'all' issues two API calls and merges them — there is no single API value for both."
        ),
    ),
    include_completed: bool = typer.Option(
        False, "--include-completed", hidden=True,
        help="Deprecated alias for --status all.",
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
    # Legacy flag: it used to map to `completed=true`, which the API reads as
    # "completed only" — the opposite of its name. It now means --status all.
    if include_completed:
        status = TaskStatusFilter.ALL

    query = TaskListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        assigned_to=assigned_to,
        assigned_to_team=assigned_to_team,
        created_by=created_by,
        completed=None if status is TaskStatusFilter.ALL else (status is TaskStatusFilter.COMPLETED),
        task_type=task_type,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    fetch = (
        (lambda c: c.list_tasks_all_statuses(query))
        if status is TaskStatusFilter.ALL
        else (lambda c: c.list_tasks(query))
    )
    output_result(run_client(token, fetch), fmt, fields=None if verbose else _DEFAULT_FIELDS)


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


@handle_errors
def add_task(
    name: str = typer.Argument(..., help="Task title/name"),
    due_date: str | None = typer.Option(
        None, "--due-date", help="Example: '2025-05-24 10:00 AM -0700' (must match Wealthbox format)"
    ),
    frame: TaskFrame | None = typer.Option(
        None, "--frame",
        help=_FRAME_HELP,
        parser=_normalize_frame,
        metavar="FRAME",
    ),
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
    custom_field: list[str] = typer.Option(
        [], "--custom-field",
        help=(
            'Set a custom field as NAME=VALUE (repeatable). Name or numeric ID; '
            'see: wbox categories custom-fields --document-type Task'
        ),
    ),
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

    async def _create(client: WealthboxClient) -> dict[str, Any]:
        if category is not None:
            payload["category"] = await resolve_category_id(client, CategoryType.TASK_CATEGORIES, category)
        payload["custom_fields"] = await resolve_custom_fields(client, DocumentType.TASK, custom_field)
        # Strip None before model construction (due_date XOR frame validator needs clean input)
        clean = {k: v for k, v in payload.items() if v is not None}
        return await client.create_task(TaskCreateInput(**clean))

    output_result(run_client(token, _create), fmt)


@handle_errors
def update_task(
    task_id: int = typer.Argument(..., help="Task ID"),
    name: str | None = typer.Option(None, "--name", help="Task name"),
    due_date: str | None = typer.Option(None, "--due-date", help="ISO 8601 datetime, e.g. '2026-04-01T09:00:00-07:00'"),
    frame: TaskFrame | None = typer.Option(
        None, "--frame",
        help=_FRAME_HELP,
        parser=_normalize_frame,
        metavar="FRAME",
    ),
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
    custom_field: list[str] = typer.Option(
        [], "--custom-field",
        help=(
            'Set a custom field as NAME=VALUE (repeatable). Name or numeric ID; '
            'see: wbox categories custom-fields --document-type Task'
        ),
    ),
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

    async def _update(client: WealthboxClient) -> dict[str, Any]:
        if category is not None:
            payload["category"] = await resolve_category_id(client, CategoryType.TASK_CATEGORIES, category)
        fields = await resolve_custom_fields(client, DocumentType.TASK, custom_field)
        if fields is not None:
            payload["custom_fields"] = fields
        return await client.update_task(task_id, TaskUpdateInput(**payload))

    output_result(run_client(token, _update), fmt)


create_resource_commands(
    app,
    ResourceSpec(
        name="tasks",
        get_func_name="get_task",
        id_arg_name="task_id",
        id_help="Task ID",
        get_client_method="get_task",
        list_help=(
            "List tasks with optional filters. Wealthbox returns open tasks only by default; "
            "use --status completed or --status all to see completed ones"
        ),
        get_help="Get a single task by ID.",
        add_help="Create a new task. Required: name, and either due_date or frame.",
        update_help="Update an existing task. Pass only the fields you want to change.",
        delete_help="Delete a task by ID.",
        list_hook=list_tasks,
        get_hook=get_task,
        add_hook=add_task,
        update_hook=update_task,
        delete_client_method="delete_task",
        delete_label="Task",
        operations=frozenset({"list", "get", "add", "update", "delete"}),
    ),
)
