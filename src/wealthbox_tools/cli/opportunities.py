from __future__ import annotations

from typing import Any

import typer

from wealthbox_tools.models import (
    OpportunityAmountKind,
    OpportunityCreateInput,
    OpportunityListQuery,
    OpportunityOrder,
    OpportunityResourceType,
    OpportunityUpdateInput,
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

app = make_resource_app(help="Manage Wealthbox opportunities.")

_DEFAULT_FIELDS = ["id", "name", "stage", "probability", "target_close", "manager", "linked_to"]
_MORE_FIELDS_RESERVED = {
    "name", "target_close", "probability", "stage", "description",
    "manager", "visible_to", "linked_to", "amounts",
}


def _build_amounts(
    fee: float | None,
    commission: float | None,
    aum: float | None,
    other: float | None,
    currency: str,
) -> list[dict[str, Any]] | None:
    amounts = []
    for value, kind in (
        (fee, OpportunityAmountKind.FEE),
        (commission, OpportunityAmountKind.COMMISSION),
        (aum, OpportunityAmountKind.AUM),
        (other, OpportunityAmountKind.OTHER),
    ):
        if value is not None:
            amounts.append({"amount": value, "currency": currency, "kind": kind})
    return amounts or None


@app.command("list", help="List opportunities with optional filters.")
@handle_errors
def list_opportunities(
    resource_id: int | None = typer.Option(
        None, "--resource-id", help="Filter by linked resource ID (requires --resource-type)"
    ),
    resource_type: OpportunityResourceType | None = typer.Option(
        None, "--resource-type", help="Filter by linked resource type: Contact, Project"
    ),
    order: OpportunityOrder | None = typer.Option(None, "--order", help="Sort order: asc, desc, recent, created"),
    include_closed: bool | None = typer.Option(
        None, "--include-closed/--no-include-closed", help="Include closed opportunities"
    ),
    updated_since: str | None = typer.Option(None, "--updated-since"),
    updated_before: str | None = typer.Option(None, "--updated-before"),
    page: int | None = typer.Option(None),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    query = OpportunityListQuery(
        resource_id=resource_id,
        resource_type=resource_type,
        order=order,
        include_closed=include_closed,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )
    output_result(
        run_client(token, lambda c: c.list_opportunities(query)), fmt, fields=None if verbose else _DEFAULT_FIELDS
    )


@app.command("get", help="Get a single opportunity by ID.")
@handle_errors
def get_opportunity(
    opportunity_id: int = typer.Argument(..., help="Opportunity ID"),
    no_comments: bool = typer.Option(False, "--no-comments", help="Omit comments from output"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    result = run_client_with_comments(
        token, lambda c: c.get_opportunity(opportunity_id),
        COMMENT_RESOURCE_TYPES["opportunities"], opportunity_id, include_comments=not no_comments,
    )
    output_get_result(result, fmt)


@app.command("add", help="Create a new opportunity.")
@handle_errors
def add_opportunity(
    name: str = typer.Argument(..., help="Opportunity name"),
    target_close: str = typer.Option(..., "--target-close", help="Target close date (e.g. 2026-06-30)"),
    probability: int = typer.Option(..., "--probability", help="Close probability 0–100"),
    stage: int = typer.Option(..., "--stage", help="Stage ID — see: wbox categories"),
    description: str | None = typer.Option(None, "--description"),
    manager: int | None = typer.Option(None, "--manager", help="Assign a manager by user ID"),
    visible_to: str | None = typer.Option(None, "--visible-to"),
    contact: int | None = typer.Option(None, "--contact", help="Link to a Contact by ID"),
    project: int | None = typer.Option(None, "--project", help="Link to a Project by ID"),
    fee: float | None = typer.Option(None, "--fee", help="Fee amount"),
    commission: float | None = typer.Option(None, "--commission", help="Commission amount"),
    aum: float | None = typer.Option(None, "--aum", help="AUM amount"),
    other_amount: float | None = typer.Option(None, "--other-amount", help="Other amount"),
    currency: str = typer.Option("USD", "--currency", help="Currency code for all amounts (default: USD)"),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="JSON object for additional fields (e.g. custom_fields)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {
        "name": name,
        "target_close": target_close,
        "probability": probability,
        "stage": stage,
        "description": description,
        "manager": manager,
        "visible_to": visible_to,
        "linked_to": build_linked_to(contact, project, None),
        "amounts": _build_amounts(fee, commission, aum, other_amount, currency),
    }

    if more_fields:
        payload.update(parse_more_fields(more_fields, _MORE_FIELDS_RESERVED))

    input_model = OpportunityCreateInput(**{k: v for k, v in payload.items() if v is not None})
    output_result(run_client(token, lambda c: c.create_opportunity(input_model)), fmt)


@app.command("update", help="Update an existing opportunity. Pass only the fields you want to change.")
@handle_errors
def update_opportunity(
    opportunity_id: int = typer.Argument(..., help="Opportunity ID"),
    name: str | None = typer.Option(None, "--name"),
    target_close: str | None = typer.Option(None, "--target-close"),
    probability: int | None = typer.Option(None, "--probability", help="Close probability 0–100"),
    stage: int | None = typer.Option(None, "--stage", help="Stage ID — see: wbox categories"),
    description: str | None = typer.Option(None, "--description"),
    manager: int | None = typer.Option(None, "--manager"),
    visible_to: str | None = typer.Option(None, "--visible-to"),
    contact: int | None = typer.Option(None, "--contact", help="Replace linked Contact (by ID)"),
    project: int | None = typer.Option(None, "--project", help="Replace linked Project (by ID)"),
    fee: float | None = typer.Option(None, "--fee", help="Fee amount"),
    commission: float | None = typer.Option(None, "--commission", help="Commission amount"),
    aum: float | None = typer.Option(None, "--aum", help="AUM amount"),
    other_amount: float | None = typer.Option(None, "--other-amount", help="Other amount"),
    currency: str = typer.Option("USD", "--currency", help="Currency code for all amounts (default: USD)"),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="JSON object for additional fields (e.g. custom_fields)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {k: v for k, v in {
        "name": name,
        "target_close": target_close,
        "probability": probability,
        "stage": stage,
        "description": description,
        "manager": manager,
        "visible_to": visible_to,
    }.items() if v is not None}

    linked = build_linked_to(contact, project, None)
    if linked is not None:
        payload["linked_to"] = linked

    amounts = _build_amounts(fee, commission, aum, other_amount, currency)
    if amounts is not None:
        payload["amounts"] = amounts

    if more_fields:
        payload.update(parse_more_fields(more_fields, _MORE_FIELDS_RESERVED))

    input_model = OpportunityUpdateInput(**payload)
    output_result(run_client(token, lambda c: c.update_opportunity(opportunity_id, input_model)), fmt)


@app.command("delete", help="Delete an opportunity by ID.")
@handle_errors
def delete_opportunity(
    opportunity_id: int = typer.Argument(..., help="Opportunity ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    run_client(token, lambda c: c.delete_opportunity(opportunity_id))
    typer.echo(f"Opportunity {opportunity_id} deleted.")
