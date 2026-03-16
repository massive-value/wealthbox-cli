from __future__ import annotations

import json
from typing import Any

import typer

from wealthbox_tools.models import ContactCreateInput, ContactListQuery, ContactUpdateInput

from wealthbox_tools.models import CategoryType, HouseholdTitle, ContactsOrder, RecordType

from ._util import active_to_status, handle_errors, make_category_command, output_result, run_client


_RECORD_TYPE_METAVAR = "[" + "|".join(m.value.lower() for m in RecordType) + "]"


def _parse_record_type(value: str | None) -> RecordType | None:
    if value is None:
        return None
    for member in RecordType:
        if member.value.lower() == value.lower():
            return member
    valid = ", ".join(m.value for m in RecordType)
    raise typer.BadParameter(f"Invalid type '{value}'. Choose from: {valid}")

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
    type_: RecordType | None = typer.Option(None, "--type", help="Record Type - Person, Household, Organization, or Trust"),
    name: str | None = typer.Option(None, help="Filter by name - Contains"),
    email: str | None = typer.Option(None, help="Filter by email - Full Match"),
    phone: str | None = typer.Option(None, help="Filter by phone - Full Match - Parsing handled by Wealthbox"),
    contact_type: str | None = typer.Option(None, "--contact-type", help="Client, Prospect, Vendor, etc. - see wbox contacts categories contact-types"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Filter by active status"),
    deleted: bool | None = typer.Option(None, "--deleted", help="Filter to deleted contacts only (omit to see non-deleted, which is the API default)"),
    household_title: HouseholdTitle | None = typer.Option(None, help="The household title you wish to filter the household title"),
    tags: str | None = typer.Option(None, help="Comma-separated tags"),
    order: ContactsOrder = typer.Option(ContactsOrder.ASC, help="The order that the contacts should be returned in"),
    updated_since: str | None = typer.Option(None, "--updated-since", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    updated_before: str | None = typer.Option(None, "--updated-before", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    deleted_since: str | None = typer.Option(None, help="Only returns deleted contacts that were deleted on or after this timestamp"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Filter by assigned user ID (client-side scan — fetches all pages)."),
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
        type=type_,
        name=name,
        email=email,
        phone=phone,
        contact_type=contact_type,
        active=active,
        deleted=deleted,
        household_title=household_title,
        tags=tag_list,
        order=order,
        updated_since=updated_since,
        updated_before=updated_before,
        deleted_since=deleted_since,
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
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    output_result(run_client(token, lambda c: c.get_contact(contact_id)), fmt)


@app.command("add", help="Create a new contact.")
@handle_errors
def add_contact(
    record_type: str | None = typer.Argument(None, metavar=_RECORD_TYPE_METAVAR, help="Contact record type (case-insensitive)"),
    # Advanced path
    json_data: str | None = typer.Option(None, "--json", help="Full contact as JSON (for complex/nested fields); must include 'type'"),
    # Common scalar flags
    first_name: str | None = typer.Option(None, "--first-name"),
    middle_name: str | None = typer.Option(None, "--middle-name"),
    last_name: str | None = typer.Option(None, "--last-name"),
    name: str | None = typer.Option(None, "--name", help="Full name (use for Household/Organization/Trust; use --first-name/--last-name for Person)"),
    job_title: str | None = typer.Option(None, "--job-title"),
    company_name: str | None = typer.Option(None, "--company-name"),
    contact_type: str | None = typer.Option(None, "--contact-type", help="e.g. Client, Prospect"),
    contact_source: str | None = typer.Option(None, "--contact-source"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Set contact status to Active or Inactive"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Assign to a user by ID"),
    email: str | None = typer.Option(None, "--email", help="Primary email address"),
    email_type: str | None = typer.Option(None, "--email-type", help="Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types"),
    phone: str | None = typer.Option(None, "--phone", help="Primary phone number"),
    phone_type: str | None = typer.Option(None, "--phone-type", help="Phone kind (e.g. Work, Mobile) — see: wbox contacts categories phone-types"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    if json_data is not None:
        parsed = json.loads(json_data)
        if "type" not in parsed:
            raise typer.BadParameter(
                "--json payload must include a 'type' field (Person, Household, Organization, Trust).",
                param_hint="--json",
            )
        input_model = ContactCreateInput(**parsed)
    else:
        if record_type is None:
            raise typer.BadParameter(
                "RECORD_TYPE argument is required. Example: wbox contacts add Person --first-name John\n"
                "To use a full JSON payload instead, pass --json '{...}' with a 'type' field.",
                param_hint="RECORD_TYPE",
            )
        resolved_type = _parse_record_type(record_type)
        payload: dict[str, Any] = {
            "type": resolved_type,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "name": name,
            "job_title": job_title,
            "company_name": company_name,
            "contact_type": contact_type,
            "contact_source": contact_source,
            "status": active_to_status(active),
            "assigned_to": assigned_to,
        }
        if email:
            email_entry: dict[str, Any] = {"address": email, "principal": True}
            if email_type:
                email_entry["kind"] = email_type
            payload["email_addresses"] = [email_entry]
        if phone:
            phone_entry: dict[str, Any] = {"address": phone, "principal": True}
            if phone_type:
                phone_entry["kind"] = phone_type
            payload["phone_numbers"] = [phone_entry]
        input_model = ContactCreateInput(**{k: v for k, v in payload.items() if v is not None})

    output_result(run_client(token, lambda c: c.create_contact(input_model)), fmt)


@app.command("update", help="Update an existing contact. Pass only the fields you want to change.")
@handle_errors
def update_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    # Advanced path for nested arrays (email_addresses, phone_numbers, etc.)
    json_data: str | None = typer.Option(None, "--json", help="Full update as JSON (for nested fields like email_addresses)"),
    # Scalar flags
    first_name: str | None = typer.Option(None, "--first-name"),
    middle_name: str | None = typer.Option(None, "--middle-name"),
    last_name: str | None = typer.Option(None, "--last-name"),
    name: str | None = typer.Option(None, "--name", help="Full name (for Household/Org/Trust)"),
    job_title: str | None = typer.Option(None, "--job-title"),
    company_name: str | None = typer.Option(None, "--company-name"),
    contact_type: str | None = typer.Option(None, "--contact-type", help="e.g. Client, Prospect"),
    contact_source: str | None = typer.Option(None, "--contact-source"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Set contact status to Active or Inactive"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Reassign to a user by ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json only for now"),
) -> None:
    if json_data is not None:
        input_model = ContactUpdateInput(**json.loads(json_data))
    else:
        payload: dict[str, Any] = {k: v for k, v in {
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "name": name,
            "job_title": job_title,
            "company_name": company_name,
            "contact_type": contact_type,
            "contact_source": contact_source,
            "status": active_to_status(active),
            "assigned_to": assigned_to,
        }.items() if v is not None}
        input_model = ContactUpdateInput(**payload)

    output_result(run_client(token, lambda c: c.update_contact(contact_id, input_model)), fmt)


@app.command("delete", help="Delete an existing contact.")
@handle_errors
def delete_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    run_client(token, lambda c: c.delete_contact(contact_id))
    typer.echo(f"Contact {contact_id} deleted.")
