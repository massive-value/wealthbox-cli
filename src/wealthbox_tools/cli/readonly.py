from __future__ import annotations

import asyncio
from typing import Optional

import typer

from wealthbox_tools.models import ActivityListQuery, ActivityTypeOptions, CategoryTypeOptions, DocumentTypeOptions
from wealthbox_tools.models.common import PaginationQuery

from ._util import get_client, handle_errors, output_result

app = typer.Typer(help="Read-only Wealthbox data.", no_args_is_help=True)


@app.command("me")
@handle_errors
def get_me(
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """Get the current authenticated user."""
    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.get_me()

    output_result(asyncio.run(_run()), fmt)


@app.command("users")
@handle_errors
def list_users(
    page: Optional[int] = typer.Option(None),
    per_page: Optional[int] = typer.Option(None, "--per-page"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List all users in the account."""
    query = PaginationQuery(page=page, per_page=per_page)

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_users(query)

    output_result(asyncio.run(_run()), fmt)


@app.command("activity")
@handle_errors
def list_activity(
    contact: Optional[int] = typer.Option(None, help="Filter by contact ID"),
    type_: Optional[ActivityTypeOptions] = typer.Option(None, "--type", help="Activity type filter"),
    updated_since: Optional[str] = typer.Option(None, "--updated-since"),
    updated_before: Optional[str] = typer.Option(None, "--updated-before"),
    page: Optional[int] = typer.Option(None),
    per_page: Optional[int] = typer.Option(None, "--per-page"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List activity feed."""
    query = ActivityListQuery(
        contact=contact,
        type=type_,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_activity(query)

    output_result(asyncio.run(_run()), fmt)


@app.command("custom-categories")
@handle_errors
def list_custom_categories(
    type_: CategoryTypeOptions = typer.Option(..., "--type", help="Custom Category Type Options"),
    document_type: Optional[DocumentTypeOptions] = typer.Option(None, "--document-type", help="Filter custom_fields by document type"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List custom categories"""
    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_custom_categories(type_, document_type=document_type)

    output_result(asyncio.run(_run()), fmt)
