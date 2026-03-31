from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import ProjectCreateInput, ProjectListQuery, ProjectUpdateInput

from ._util import (
    COMMENT_RESOURCE_TYPES,
    OutputFormat,
    handle_errors,
    make_resource_app,
    output_get_result,
    output_result,
    parse_more_fields,
    run_client,
    run_client_with_comments,
)

app = make_resource_app(help="Manage Wealthbox projects.")

_DEFAULT_FIELDS = ["id", "name", "description", "organizer", "updated_at"]


@app.command("list", help="List projects with optional date range filters.")
@handle_errors
def list_projects(
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = ProjectListQuery(
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )
    output_result(run_client(token, lambda c: c.list_projects(query)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("get", help="Get a single project by ID.")
@handle_errors
def get_project(
    project_id: int = typer.Argument(..., help="Project ID"),
    no_comments: bool = typer.Option(False, "--no-comments", help="Omit comments from output"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    result = run_client_with_comments(
        token, lambda c: c.get_project(project_id),
        COMMENT_RESOURCE_TYPES["projects"], project_id, include_comments=not no_comments,
    )
    output_get_result(result, fmt)


@app.command("add", help="Create a new project.")
@handle_errors
def add_project(
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option(..., "--description", help="Project description"),
    organizer: int | None = typer.Option(None, "--organizer", help="Organizer user ID"),
    visible_to: str | None = typer.Option(None, "--visible-to"),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="JSON object for additional fields (e.g. custom_fields)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {
        "name": name,
        "description": description,
        "organizer": organizer,
        "visible_to": visible_to,
    }

    if more_fields:
        payload.update(parse_more_fields(more_fields, {"name", "description", "organizer", "visible_to"}))

    input_model = ProjectCreateInput(**{k: v for k, v in payload.items() if v is not None})
    output_result(run_client(token, lambda c: c.create_project(input_model)), fmt)


@app.command("update", help="Update an existing project. Pass only the fields you want to change.")
@handle_errors
def update_project(
    project_id: int = typer.Argument(..., help="Project ID"),
    name: str | None = typer.Option(None, "--name"),
    description: str | None = typer.Option(None, "--description"),
    organizer: int | None = typer.Option(None, "--organizer", help="Organizer user ID"),
    visible_to: str | None = typer.Option(None, "--visible-to"),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="JSON object for additional fields (e.g. custom_fields)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {k: v for k, v in {
        "name": name,
        "description": description,
        "organizer": organizer,
        "visible_to": visible_to,
    }.items() if v is not None}

    if more_fields:
        payload.update(parse_more_fields(more_fields, {"name", "description", "organizer", "visible_to"}))

    input_model = ProjectUpdateInput(**payload)
    output_result(run_client(token, lambda c: c.update_project(project_id, input_model)), fmt)
