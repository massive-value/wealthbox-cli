from __future__ import annotations

import json
from typing import Any

import typer

from wealthbox_tools.models import (
    CategoryType,
    ContactCreateInput,
    ContactListQuery,
    ContactsOrder,
    ContactUpdateInput,
    Gender,
    HouseholdTitle,
    MaritalStatus,
    RecordType,
)

from ._util import (
    OutputFormat,
    active_to_status,
    handle_errors,
    make_category_command,
    make_resource_app,
    output_result,
    parse_more_fields,
    run_client,
)

app = make_resource_app(help="Manage Wealthbox contacts.")

_DEFAULT_FIELDS = ["id", "name", "type", "contact_type", "assigned_to", "status"]

# -- categories sub-app -------------------------------------------------------
categories_app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="List available category values for contact fields.",
    no_args_is_help=True,
)
categories_app.command("contact-types", help="List contact type options.")(
    make_category_command(CategoryType.CONTACT_TYPES)
)
categories_app.command("contact-sources", help="List contact source options.")(
    make_category_command(CategoryType.CONTACT_SOURCES)
)
categories_app.command("email-types", help="List email type options.")(make_category_command(CategoryType.EMAIL_TYPES))
categories_app.command("phone-types", help="List phone type options.")(make_category_command(CategoryType.PHONE_TYPES))
categories_app.command("address-types", help="List address type options.")(
    make_category_command(CategoryType.ADDRESS_TYPES)
)
categories_app.command("website-types", help="List website type options.")(
    make_category_command(CategoryType.WEBSITE_TYPES)
)
categories_app.command("contact-roles", help="List contact role options.")(
    make_category_command(CategoryType.CONTACT_ROLES)
)
app.add_typer(categories_app, name="categories")


@app.command("list", help="List contacts with optional filters.")
@handle_errors
def list_contacts(
    type_: RecordType | None = typer.Option(
        None, "--type", help="Record Type - Person, Household, Organization, or Trust"
    ),
    name: str | None = typer.Option(None, help="Filter by name - Contains"),
    email: str | None = typer.Option(None, help="Filter by email - Full Match"),
    phone: str | None = typer.Option(None, help="Filter by phone - Full Match - Parsing handled by Wealthbox"),
    contact_type: str | None = typer.Option(
        None, "--contact-type", help="Client, Prospect, Vendor, etc. - see wbox contacts categories contact-types"
    ),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Filter by active status"),
    deleted: bool | None = typer.Option(
        None, "--deleted", help="Filter to deleted contacts only (omit to see non-deleted, which is the API default)"
    ),
    household_title: HouseholdTitle | None = typer.Option(
        None, help="The household title you wish to filter the household title"
    ),
    tags: str | None = typer.Option(None, help="Comma-separated tags"),
    order: ContactsOrder = typer.Option(ContactsOrder.ASC, help="The order that the contacts should be returned in"),
    updated_since: str | None = typer.Option(None, "--updated-since", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    updated_before: str | None = typer.Option(None, "--updated-before", help="Format of 'YYYY-MM-DD 07:00 AM -0700'"),
    deleted_since: str | None = typer.Option(
        None, help="Only returns deleted contacts that were deleted on or after this timestamp"
    ),
    assigned_to: int | None = typer.Option(
        None, "--assigned-to", help="Filter by assigned user ID (client-side scan — fetches all pages)."
    ),
    page: int | None = typer.Option(None, help="Page number"),
    per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
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
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.get_contact(contact_id)), fmt)


# -- add sub-app --------------------------------------------------------------
add_app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Create a new contact.",
    no_args_is_help=True,
)
app.add_typer(add_app, name="add")

_PERSON_RESERVED = {
    "type", "first_name", "middle_name", "last_name", "prefix", "suffix", "nickname",
    "gender", "marital_status", "birth_date", "anniversary", "job_title", "company_name",
    "contact_type", "contact_source", "status", "assigned_to", "email_addresses", "phone_numbers",
}
_HOUSEHOLD_RESERVED = {"type", "name", "contact_type", "contact_source", "status", "assigned_to", "email_addresses"}
_ORG_TRUST_RESERVED = _HOUSEHOLD_RESERVED | {"phone_numbers"}


def _build_contact_entry(value: str | None, kind: str | None) -> list[dict[str, Any]] | None:
    if not value:
        return None
    entry: dict[str, Any] = {"address": value, "principal": True}
    if kind:
        entry["kind"] = kind
    return [entry]


def _create_named_contact(
    record_type: RecordType,
    reserved: set[str],
    name: str,
    contact_type: str | None,
    contact_source: str | None,
    active: bool | None,
    assigned_to: int | None,
    email: str | None,
    email_type: str | None,
    phone: str | None,
    phone_type: str | None,
    more_fields: str | None,
    token: str | None,
    fmt: OutputFormat,
) -> None:
    payload: dict[str, Any] = {k: v for k, v in {
        "type": record_type,
        "name": name,
        "contact_type": contact_type,
        "contact_source": contact_source,
        "status": active_to_status(active),
        "assigned_to": assigned_to,
    }.items() if v is not None}
    emails = _build_contact_entry(email, email_type)
    if emails:
        payload["email_addresses"] = emails
    phones = _build_contact_entry(phone, phone_type)
    if phones:
        payload["phone_numbers"] = phones
    if more_fields:
        payload.update(parse_more_fields(more_fields, reserved))
    input_model = ContactCreateInput(**payload)
    output_result(run_client(token, lambda c: c.create_contact(input_model)), fmt)


@add_app.command("person", help="Create a Person contact.")
@handle_errors
def add_person(
    first_name: str | None = typer.Option(None, "--first-name"),
    middle_name: str | None = typer.Option(None, "--middle-name"),
    last_name: str | None = typer.Option(None, "--last-name"),
    prefix: str | None = typer.Option(None, "--prefix"),
    suffix: str | None = typer.Option(None, "--suffix"),
    nickname: str | None = typer.Option(None, "--nickname"),
    gender: Gender | None = typer.Option(None, "--gender"),
    marital_status: MaritalStatus | None = typer.Option(None, "--marital-status"),
    birth_date: str | None = typer.Option(None, "--birth-date", help="Format: YYYY-MM-DD"),
    anniversary: str | None = typer.Option(None, "--anniversary", help="Format: YYYY-MM-DD"),
    job_title: str | None = typer.Option(None, "--job-title"),
    company_name: str | None = typer.Option(None, "--company-name"),
    contact_type: str | None = typer.Option(None, "--contact-type", help="e.g. Client, Prospect"),
    contact_source: str | None = typer.Option(None, "--contact-source"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Set contact status to Active or Inactive"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Assign to a user by ID"),
    email: str | None = typer.Option(None, "--email", help="Primary email address"),
    email_type: str | None = typer.Option(
        None, "--email-type", help="Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types"
    ),
    phone: str | None = typer.Option(None, "--phone", help="Primary phone number"),
    phone_type: str | None = typer.Option(
        None, "--phone-type", help="Phone kind (e.g. Work, Mobile) — see: wbox contacts categories phone-types"
    ),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="Extra fields as JSON object (merged with flags; cannot override explicit flags)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {k: v for k, v in {
        "type": RecordType.PERSON,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "prefix": prefix,
        "suffix": suffix,
        "nickname": nickname,
        "gender": gender,
        "marital_status": marital_status,
        "birth_date": birth_date,
        "anniversary": anniversary,
        "job_title": job_title,
        "company_name": company_name,
        "contact_type": contact_type,
        "contact_source": contact_source,
        "status": active_to_status(active),
        "assigned_to": assigned_to,
    }.items() if v is not None}
    emails = _build_contact_entry(email, email_type)
    if emails:
        payload["email_addresses"] = emails
    phones = _build_contact_entry(phone, phone_type)
    if phones:
        payload["phone_numbers"] = phones
    if more_fields:
        payload.update(parse_more_fields(more_fields, _PERSON_RESERVED))
    input_model = ContactCreateInput(**payload)
    output_result(run_client(token, lambda c: c.create_contact(input_model)), fmt)


@add_app.command("household", help="Create a Household contact.")
@handle_errors
def add_household(
    name: str = typer.Option(..., "--name", help="Household name (required)"),
    contact_type: str | None = typer.Option(None, "--contact-type", help="e.g. Client, Prospect"),
    contact_source: str | None = typer.Option(None, "--contact-source"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Set contact status to Active or Inactive"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Assign to a user by ID"),
    email: str | None = typer.Option(None, "--email", help="Primary email address"),
    email_type: str | None = typer.Option(
        None, "--email-type", help="Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types"
    ),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="Extra fields as JSON object (merged with flags; cannot override explicit flags)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload: dict[str, Any] = {k: v for k, v in {
        "type": RecordType.HOUSEHOLD,
        "name": name,
        "contact_type": contact_type,
        "contact_source": contact_source,
        "status": active_to_status(active),
        "assigned_to": assigned_to,
    }.items() if v is not None}
    emails = _build_contact_entry(email, email_type)
    if emails:
        payload["email_addresses"] = emails
    if more_fields:
        payload.update(parse_more_fields(more_fields, _HOUSEHOLD_RESERVED))
    input_model = ContactCreateInput(**payload)
    output_result(run_client(token, lambda c: c.create_contact(input_model)), fmt)


@add_app.command("org", help="Create an Organization contact.")
@handle_errors
def add_org(
    name: str = typer.Option(..., "--name", help="Organization name (required)"),
    contact_type: str | None = typer.Option(None, "--contact-type", help="e.g. Client, Prospect"),
    contact_source: str | None = typer.Option(None, "--contact-source"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Set contact status to Active or Inactive"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Assign to a user by ID"),
    email: str | None = typer.Option(None, "--email", help="Primary email address"),
    email_type: str | None = typer.Option(
        None, "--email-type", help="Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types"
    ),
    phone: str | None = typer.Option(None, "--phone", help="Primary phone number"),
    phone_type: str | None = typer.Option(
        None, "--phone-type", help="Phone kind (e.g. Work, Mobile) — see: wbox contacts categories phone-types"
    ),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="Extra fields as JSON object (merged with flags; cannot override explicit flags)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    _create_named_contact(
        RecordType.ORGANIZATION, _ORG_TRUST_RESERVED, name, contact_type, contact_source,
        active, assigned_to, email, email_type, phone, phone_type, more_fields, token, fmt,
    )


@add_app.command("trust", help="Create a Trust contact.")
@handle_errors
def add_trust(
    name: str = typer.Option(..., "--name", help="Trust name (required)"),
    contact_type: str | None = typer.Option(None, "--contact-type", help="e.g. Client, Prospect"),
    contact_source: str | None = typer.Option(None, "--contact-source"),
    active: bool | None = typer.Option(None, "--active/--inactive", help="Set contact status to Active or Inactive"),
    assigned_to: int | None = typer.Option(None, "--assigned-to", help="Assign to a user by ID"),
    email: str | None = typer.Option(None, "--email", help="Primary email address"),
    email_type: str | None = typer.Option(
        None, "--email-type", help="Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types"
    ),
    phone: str | None = typer.Option(None, "--phone", help="Primary phone number"),
    phone_type: str | None = typer.Option(
        None, "--phone-type", help="Phone kind (e.g. Work, Mobile) — see: wbox contacts categories phone-types"
    ),
    more_fields: str | None = typer.Option(
        None, "--more-fields", help="Extra fields as JSON object (merged with flags; cannot override explicit flags)"
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    _create_named_contact(
        RecordType.TRUST, _ORG_TRUST_RESERVED, name, contact_type, contact_source,
        active, assigned_to, email, email_type, phone, phone_type, more_fields, token, fmt,
    )


@app.command("update", help="Update an existing contact. Pass only the fields you want to change.")
@handle_errors
def update_contact(
    contact_id: int = typer.Argument(..., help="Contact ID"),
    # Advanced path for nested arrays (email_addresses, phone_numbers, etc.)
    json_data: str | None = typer.Option(
        None, "--json", help="Full update as JSON (for nested fields like email_addresses)"
    ),
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
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
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
