from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import (
    WorkflowCreateInput,
    WorkflowListQuery,
    WorkflowResourceType,
    WorkflowStatus,
    WorkflowStepCompleteInput,
    WorkflowTemplateListQuery,
)

from ._util import (
    COMMENT_RESOURCE_TYPES,
    OutputFormat,
    build_linked_to,
    handle_errors,
    make_resource_app,
    output_get_result,
    output_result,
    parse_more_fields,
    run_client,
    run_client_with_comments,
)

app = make_resource_app(help="Manage Wealthbox workflows.")

templates_app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="List workflow templates.",
    no_args_is_help=True,
)
app.add_typer(templates_app, name="templates")

_DEFAULT_FIELDS = ["id", "label", "linked_to", "created_at", "completed_at"]
_GET_DEFAULT_FIELDS = [
    "id", "name", "label", "completed_at", "started_at",
    "linked_to", "active_step", "workflow_steps",
]
_TEMPLATE_DEFAULT_FIELDS = ["id", "name", "description", "status"]


@app.command("list", help="List workflows with optional filters.")
@handle_errors
def list_workflows(
    resource_id: int | None = typer.Option(
        None, "--resource-id", help="Filter by linked resource ID (requires --resource-type)"
    ),
    resource_type: WorkflowResourceType | None = typer.Option(
        None, "--resource-type", help="Filter by linked resource type: Contact, Project"
    ),
    status: WorkflowStatus | None = typer.Option(None, "--status", help="active, completed, or scheduled"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = WorkflowListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        status=status,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )
    output_result(
        run_client(token, lambda c: c.list_workflows(query)), fmt, fields=None if verbose else _DEFAULT_FIELDS
    )


@app.command("get", help="Get a single workflow by ID.")
@handle_errors
def get_workflow(
    workflow_id: int = typer.Argument(..., help="Workflow ID"),
    no_comments: bool = typer.Option(False, "--no-comments", help="Omit comments from output"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields including the full template"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    result = run_client_with_comments(
        token, lambda c: c.get_workflow(workflow_id),
        COMMENT_RESOURCE_TYPES["workflows"], workflow_id, include_comments=not no_comments,
    )
    fields = None if verbose else (_GET_DEFAULT_FIELDS + (["comments"] if not no_comments else []))
    output_get_result(result, fmt, fields=fields)


@app.command("add", help="Create a new workflow from a template.")
@handle_errors
def add_workflow(
    template: int = typer.Option(..., "--template", help="Workflow template ID — see: wbox workflows templates list"),
    label: str | None = typer.Option(None, "--label", help="Optional label for this workflow instance"),
    contact: int | None = typer.Option(None, "--contact", help="Link to a Contact by ID"),
    project: int | None = typer.Option(None, "--project", help="Link to a Project by ID"),
    opportunity: int | None = typer.Option(None, "--opportunity", help="Link to an Opportunity by ID"),
    visible_to: str | None = typer.Option(None, "--visible-to"),
    starts_at: str | None = typer.Option(None, "--starts-at", help="Start date (e.g. 2026-06-01)"),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="JSON object for additional fields (e.g. workflow_milestones)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {
        "workflow_template": template,
        "label": label,
        "visible_to": visible_to,
        "starts_at": starts_at,
        "linked_to": build_linked_to(contact, project, opportunity),
    }

    if more_fields:
        _reserved = {"workflow_template", "label", "visible_to", "starts_at", "linked_to"}
        payload.update(parse_more_fields(more_fields, _reserved))

    input_model = WorkflowCreateInput(**{k: v for k, v in payload.items() if v is not None})
    output_result(run_client(token, lambda c: c.create_workflow(input_model)), fmt)


@app.command("next", help="Show the active step (or completion status) of a workflow.")
@handle_errors
def next_workflow_step(
    workflow_id: int = typer.Argument(..., help="Workflow ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    workflow = run_client(token, lambda c: c.get_workflow(workflow_id))
    if workflow.get("completed_at"):
        # Wealthbox doesn't clear `active_step` when a workflow completes — it
        # still points at the final step. Echoing that is misleading. Emit a
        # completion marker instead so callers can branch on a stable shape.
        output_result(
            {"completed": True, "completed_at": workflow["completed_at"]}, fmt
        )
        return
    output_result(workflow.get("active_step") or {}, fmt)


@app.command("complete-step", help="Mark a workflow step as complete.")
@handle_errors
def complete_workflow_step(
    workflow_id: int = typer.Argument(..., help="Workflow ID"),
    step_id: int = typer.Argument(..., help="Step ID"),
    outcome_id: int | None = typer.Option(
        None, "--outcome-id", help="Workflow outcome ID (if step has multiple outcomes)"
    ),
    due_date: str | None = typer.Option(
        None, "--due-date", help="Due date when restarting a step (requires --due-date-set)"
    ),
    due_date_set: bool = typer.Option(False, "--due-date-set", help="Whether the restarted step has a due date"),
    no_advance_hint: bool = typer.Option(
        False, "--no-advance-hint",
        help="Skip the follow-up workflow fetch + stderr summary of the new active step",
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    data = WorkflowStepCompleteInput(
        workflow_outcome_id=outcome_id,
        due_date_set=due_date_set,
        due_date=due_date,
    )
    output_result(run_client(token, lambda c: c.complete_workflow_step(workflow_id, step_id, data)), fmt)
    if not no_advance_hint:
        workflow = run_client(token, lambda c: c.get_workflow(workflow_id))
        _emit_advance_hint(workflow)


def _emit_advance_hint(workflow: dict[str, Any]) -> None:
    """Print a one-line summary of the workflow's new state to stderr.

    The Wealthbox `complete-step` response doesn't say which outcome was
    selected or where the workflow advanced to, so we follow up with a
    workflow fetch and surface that signal here.
    """
    if workflow.get("completed_at"):
        typer.echo("✓ Workflow completed.", err=True)
        return
    active = workflow.get("active_step") or {}
    active_id = active.get("id")
    active_name = active.get("name")
    if active_id and active_name:
        typer.echo(f"→ Active step: {active_name} (id {active_id})", err=True)


@app.command("revert-step", help="Revert a completed workflow step.")
@handle_errors
def revert_workflow_step(
    workflow_id: int = typer.Argument(..., help="Workflow ID"),
    step_id: int = typer.Argument(..., help="Step ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.revert_workflow_step(workflow_id, step_id)), fmt)


@templates_app.command("list", help="List available workflow templates.")
@handle_errors
def list_workflow_templates(
    resource_id: int | None = typer.Option(None, "--resource-id", help="Filter by linked resource ID"),
    resource_type: WorkflowResourceType | None = typer.Option(
        None, "--resource-type", help="Filter by linked resource type: Contact, Project"
    ),
    status: WorkflowStatus | None = typer.Option(None, "--status", help="active, completed, or scheduled"),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = WorkflowTemplateListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        status=status,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )
    output_result(
        run_client(token, lambda c: c.list_workflow_templates(query)),
        fmt,
        fields=None if verbose else _TEMPLATE_DEFAULT_FIELDS,
    )
