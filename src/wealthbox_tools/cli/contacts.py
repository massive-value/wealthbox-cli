from __future__ import annotations

import asyncio
import json
from typing import Optional

import typer

from wealthbox_tools.models import ContactCreateInput, ContactListQuery, ContactUpdateInput

from wealthbox_tools.models import HouseholdTitleOptions, ContactsOrderOptions, ContactTypeOptions, RecordTypeOptions

from ._util import get_client, handle_errors, output_result

app = typer.Typer(help="Manage Wealthbox contacts.", no_args_is_help=True)


@app.command("list")
@handle_errors
def list_contacts(
    contact_type: Optional[ContactTypeOptions] = typer.Option(None, "--contact-type", help="Client, Prospect, Vendor, etc."),
    name: Optional[str] = typer.Option(None, help="Filter by name - Contains"),
    email: Optional[str] = typer.Option(None, help="Filter by email - Full Match"),
    phone: Optional[str] = typer.Option(None, help="Filter by phone - Full Match - Parsing handled by Wealthbox"),
    active: Optional[bool] = typer.Option(None, help="Filter by active status"),
    tags: Optional[str] = typer.Option(None, help="Comma-separated tags"),
    deleted: Optional[bool] = typer.Option(None, help="Only returns contacts whose active flag match the specified value"),
    deleted_since: Optional[str] = typer.Option(None, help="Only returns deleted contacts that were deleted on or after this timestamp"),
    household_title: Optional[HouseholdTitleOptions] = typer.Option(None, help="The household title you wish to filter the household title"),
    type_: Optional[RecordTypeOptions] = typer.Option(None, "--type", help="Record Type - Person, Household, Organization, or Trust"),
    order: Optional[ContactsOrderOptions] = typer.Option(None, help="The order that the contacts should be returned in"),
    updated_since: Optional[str] = typer.Option(None, "--updated-since", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    updated_before: Optional[str] = typer.Option(None, "--updated-before", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    page: Optional[int] = typer.Option(None, help="Page number"),
    per_page: Optional[int] = typer.Option(None, "--per-page", help="Results per page"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
) -> None:
    """List contacts with optional filters."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    query = ContactListQuery(
        contact_type=contact_type,
        name=name,
        email=email,
        phone=phone,
        tags=tag_list,
        active=active,
        deleted=deleted,
        deleted_since=deleted_since,
        household_title=household_title,
        type=type_,
        order=order,
        updated_since=updated_since,
        updated_before=updated_before,
        page=page,
        per_page=per_page,
    )

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.list_contacts(query)

    output_result(asyncio.run(_run()), fmt)


@app.command("get")
@handle_errors
def get_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
) -> None:
    """Get a single contact by ID."""
    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.get_contact(contact_id)

    output_result(asyncio.run(_run()), fmt)


@app.command("create")
@handle_errors
def create_contact(
    data: str = typer.Argument(..., help="JSON object of contact fields"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
) -> None:
    """Create a new contact. Pass fields as a JSON string."""
    input_model = ContactCreateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.create_contact(input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("update")
@handle_errors
def update_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    data: str = typer.Argument(..., help="JSON object of fields to update"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
) -> None:
    """Update an existing contact. Pass changed fields as a JSON string."""
    input_model = ContactUpdateInput(**json.loads(data))

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.update_contact(contact_id, input_model)

    output_result(asyncio.run(_run()), fmt)


@app.command("delete")
@handle_errors
def delete_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    """Delete a contact by ID."""
    async def _run() -> None:
        async with get_client(token) as client:
            await client.delete_contact(contact_id)

    asyncio.run(_run())
    typer.echo(f"Contact {contact_id} deleted.")
