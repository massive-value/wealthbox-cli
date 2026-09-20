from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.client import WealthboxClient
from wealthbox_tools.models import (
    WorkflowCreateInput,
    WorkflowListQuery,
    WorkflowResourceType,
    WorkflowStatus,
    WorkflowStatusFilter,
    WorkflowStepCompleteInput,
    WorkflowTemplateListQuery,
)

from ._util import (
    OutputFormat,
    ResourceSpec,
    build_linked_to,
    create_resource_commands,
    handle_errors,
    make_resource_app,
    output_result,
    parse_more_fields,
    run_client,
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
    "linked_to", "active_step", "workflow_steps", "comments",
]
_TEMPLATE_DEFAULT_FIELDS = ["id", "name", "description", "status"]


@handle_errors
def list_workflows(
    resource_id: int | None = typer.Option(
        None, "--resource-id", help="Filter by linked resource ID (requires --resource-type)"
    ),
    resource_type: WorkflowResourceType | None = typer.Option(
        None, "--resource-type", help="Filter by linked resource type: Contact, Project"
    ),
    status: WorkflowStatusFilter = typer.Option(
        WorkflowStatusFilter.ACTIVE, "--status",
        help=(
            "Which workflows to return: active (Wealthbox's own default), completed, scheduled, "
            "or all. 'all' issues one API call per status and merges them."
        ),
    ),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    all_statuses = status is WorkflowStatusFilter.ALL
    query = WorkflowListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        status=None if all_statuses else WorkflowStatus(status.value),
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )
    fetch = (
        (lambda c: c.list_workflows_all_statuses(query))
        if all_statuses
        else (lambda c: c.list_workflows(query))
    )
    output_result(run_client(token, fetch), fmt, fields=None if verbose else _DEFAULT_FIELDS)


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


create_resource_commands(
    app,
    ResourceSpec(
        name="workflows",
        get_func_name="get_workflow",
        id_arg_name="workflow_id",
        id_help="Workflow ID",
        get_client_method="get_workflow",
        list_help=(
            "List workflows with optional filters. Wealthbox returns active workflows only by "
            "default; use --status completed/scheduled/all to see the rest"
        ),
        get_help="Get a single workflow by ID.",
        add_help="Create a new workflow from a template.",
        get_supports_verbose=True,
        get_verbose_help="Show all fields including the full template",
        get_default_fields=_GET_DEFAULT_FIELDS,
        list_hook=list_workflows,
        add_hook=add_workflow,
        operations=frozenset({"list", "get", "add"}),
    ),
)


@app.command(
    "next",
    help="Show the active step of a workflow, including the outcome IDs it offers (or completion status).",
)
@handle_errors
def next_workflow_step(
    workflow_id: int = typer.Argument(..., help="Workflow ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    workflow = run_client(token, lambda c: c.get_workflow(workflow_id))
    state = _workflow_state(workflow)
    output_result(state, fmt)
    _emit_outcome_hint(state)


@app.command("complete-step", help="Mark a workflow step as complete.")
@handle_errors
def complete_workflow_step(
    workflow_id: int = typer.Argument(..., help="Workflow ID"),
    step_id: int = typer.Argument(..., help="Step ID"),
    outcome_id: int | None = typer.Option(
        None, "--outcome-id",
        help="Workflow outcome ID (if the step offers outcomes) — run `wbox workflows next ID` to list them",
    ),
    due_date: str | None = typer.Option(
        None, "--due-date", help="Due date when restarting a step (requires --due-date-set)"
    ),
    due_date_set: bool = typer.Option(False, "--due-date-set", help="Whether the restarted step has a due date"),
    no_advance_hint: bool = typer.Option(
        False, "--no-advance-hint",
        help="Skip the follow-up GET that summarizes the new active step (saves one API call).",
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    data = WorkflowStepCompleteInput(
        workflow_outcome_id=outcome_id,
        due_date_set=due_date_set,
        due_date=due_date,
    )

    async def _do(client: WealthboxClient) -> tuple[dict[str, Any], dict[str, Any] | None]:
        step_resp = await client.complete_workflow_step(workflow_id, step_id, data)
        workflow = None if no_advance_hint else await client.get_workflow(workflow_id)
        return step_resp, workflow

    step_resp, workflow = run_client(token, _do)
    output_result(step_resp, fmt)
    if workflow is not None:
        _emit_advance_hint(workflow)


_OUTCOME_FIELDS = ("id", "name", "action", "go_to_step_id")


def _slim_outcomes(step: dict[str, Any]) -> list[dict[str, Any]]:
    """Reduce a step's ``workflow_outcomes`` to the fields needed to pick one."""
    return [
        {k: o.get(k) for k in _OUTCOME_FIELDS}
        for o in (step.get("workflow_outcomes") or [])
        if isinstance(o, dict)
    ]


def _workflow_state(workflow: dict[str, Any]) -> dict[str, Any]:
    """Normalize a workflow into a "what's next" payload.

    Wealthbox does not clear `active_step` on completion — it keeps pointing
    at the final step — so consumers must check `completed_at` first.

    When the active step offers outcomes, they are slimmed to the four fields
    a caller needs to choose one. `complete-step --outcome-id` is the only way
    to advance such a step, and the ids appear nowhere else in the CLI, so
    `next` is where they have to show up.
    """
    if workflow.get("completed_at"):
        return {"completed": True, "completed_at": workflow["completed_at"]}
    step = workflow.get("active_step") or {}
    outcomes = _slim_outcomes(step)
    if outcomes:
        return {**step, "workflow_outcomes": outcomes}
    return step


def _emit_outcome_hint(state: dict[str, Any]) -> None:
    """List the active step's outcome IDs on stderr so stdout stays pipeable.

    Tabular formats flatten nested lists into one unreadable cell, so the
    outcomes get their own readable lines regardless of --format.
    """
    outcomes = state.get("workflow_outcomes") or []
    if not outcomes:
        return
    typer.echo("Outcomes for this step (pass one to `complete-step --outcome-id`):", err=True)
    for o in outcomes:
        goto = f" -> step {o['go_to_step_id']}" if o.get("go_to_step_id") else ""
        typer.echo(f"  {o.get('id')}  {o.get('name')} [{o.get('action')}]{goto}", err=True)


def _emit_advance_hint(workflow: dict[str, Any]) -> None:
    """Print a one-line summary of the workflow's new state to stderr."""
    state = _workflow_state(workflow)
    if state.get("completed"):
        typer.echo("Workflow completed.", err=True)
    elif state.get("id") and state.get("name"):
        typer.echo(f"-> Active step: {state['name']} (id {state['id']})", err=True)
        _emit_outcome_hint(state)


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
