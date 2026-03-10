from __future__ import annotations

import json

import typer

from wealthbox_tools.models import ContactCreateInput, ContactListQuery, ContactUpdateInput

from wealthbox_tools.models import CategoryType, HouseholdTitle, ContactsOrder, RecordType

from ._util import handle_errors, make_category_command, output_result, run_client

app = typer.Typer(help="Manage Wealthbox contacts.", no_args_is_help=True)

_DEFAULT_FIELDS = ["id", "name", "type", "contact_type", "assigned_to", "status"]

# -- categories sub-app -------------------------------------------------------
categories_app = typer.Typer(help="List available category values for contact fields.", no_args_is_help=True)
categories_app.command("contact-types", help="List contact type options.")(make_category_command(CategoryType.CONTACT_TYPES))
categories_app.command("contact-sources", help="List contact source options.")(make_category_command(CategoryType.CONTACT_SOURCES))
categories_app.command("email-types", help="List email type options.")(make_category_command(CategoryType.EMAIL_TYPES))
categories_app.command("phone-types", help="List phone type options.")(make_category_command(CategoryType.PHONE_TYPES))
categories_app.command("address-types", help="List address type options.")(make_category_command(CategoryType.ADDRESS_TYPES))
categories_app.command("website-types", help="List website type options.")(make_category_command(CategoryType.WEBSITE_TYPES))
categories_app.command("contact-roles", help="List contact role options.")(make_category_command(CategoryType.CONTACT_ROLES))
app.add_typer(categories_app, name="categories")


@app.command("list", help="List contacts with optional filters.")
@handle_errors
def list_contacts(
    contact_type: str | None = typer.Option(None, "--contact-type", help="Client, Prospect, Vendor, etc."),
    name: str | None = typer.Option(None, help="Filter by name - Contains"),
    email: str | None = typer.Option(None, help="Filter by email - Full Match"),
    phone: str | None = typer.Option(None, help="Filter by phone - Full Match - Parsing handled by Wealthbox"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Filter by active status"),
    tags: str | None = typer.Option(None, help="Comma-separated tags"),
    deleted: bool | None = typer.Option(None, "--deleted", help="Filter to deleted contacts only (omit to see non-deleted, which is the API default)"),
    deleted_since: str | None = typer.Option(None, help="Only returns deleted contacts that were deleted on or after this timestamp"),
    household_title: HouseholdTitle | None = typer.Option(None, help="The household title you wish to filter the household title"),
    type_: RecordType | None = typer.Option(None, "--type", help="Record Type - Person, Household, Organization, or Trust"),
    order: ContactsOrder | None = typer.Option(None, help="The order that the contacts should be returned in"),
    updated_since: str | None = typer.Option(None, "--updated-since", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    updated_before: str | None = typer.Option(None, "--updated-before", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    assigned_to: int | None = typer.Option(
        None, "--assigned-to",
        help="Filter by assigned user ID (client-side scan — fetches all pages).",
    ),
    page: int | None = typer.Option(None, help="Page number"),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    if assigned_to is not None:
        if page is not None or per_page is not None:
            typer.echo("Warning: --page and --per-page are ignored when --assigned-to is active.", err=True)
        typer.echo("Note: --assigned-to requires fetching all contacts. This may take a moment.", err=True)

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
        page=None if assigned_to is not None else page,
        per_page=None if assigned_to is not None else per_page,
    )

    if assigned_to is not None:
        def _progress(page_num: int, total_fetched: int) -> None:
            typer.echo(f"Scanning page {page_num}... ({total_fetched} fetched so far)", err=True)

        raw = run_client(token, lambda c: c.list_all_contacts(query, on_progress=_progress))
        matched = [c for c in raw.get("contacts", []) if c.get("assigned_to") == assigned_to]
        result = {"contacts": matched, "meta": {"total_count": len(matched)}}
    else:
        result = run_client(token, lambda c: c.list_contacts(query))

    output_result(result, fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("get", help="Get a single contact by ID.")
@handle_errors
def get_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    output_result(run_client(token, lambda c: c.get_contact(contact_id)), fmt, fields=None if verbose else _DEFAULT_FIELDS)


@app.command("create", help="Create a new contact. Pass fields as a JSON string.")
@handle_errors
def create_contact(
    data: str = typer.Argument(..., help="JSON object of contact fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    input_model = ContactCreateInput(**json.loads(data))

    output_result(run_client(token, lambda c: c.create_contact(input_model)), fmt)


@app.command("update", help="Update an existing contact. Pass changed fields as a JSON string.")
@handle_errors
def update_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    data: str = typer.Argument(..., help="JSON object of fields to update"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    input_model = ContactUpdateInput(**json.loads(data))

    output_result(run_client(token, lambda c: c.update_contact(contact_id, input_model)), fmt)


@app.command("delete", help="Delete an existing contact.")
@handle_errors
def delete_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    run_client(token, lambda c: c.delete_contact(contact_id))
    typer.echo(f"Contact {contact_id} deleted.")
