from __future__ import annotations

import json
from typing import Any

import typer

from wealthbox_tools.client import WealthboxClient
from wealthbox_tools.models import (
    CategoryListQuery,
    CategoryType,
    CustomFieldValue,
    DocumentType,
    LinkedToRef,
    TaskResourceType,
)


def active_to_status(active: bool | None) -> str | None:
    """Map --active/--inactive flag to Wealthbox status string."""
    if active is True:
        return "Active"
    if active is False:
        return "Inactive"
    return None


def build_linked_to(
    contact: int | None,
    project: int | None,
    opportunity: int | None,
) -> list[LinkedToRef] | None:
    """Build a linked_to list from typed ID options. Returns None if none provided."""
    refs: list[LinkedToRef] = []
    if contact is not None:
        refs.append(LinkedToRef(id=contact, type="Contact"))
    if project is not None:
        refs.append(LinkedToRef(id=project, type="Project"))
    if opportunity is not None:
        refs.append(LinkedToRef(id=opportunity, type="Opportunity"))
    return refs if refs else None


def build_resource_filter(
    contact: int | None,
    project: int | None,
    opportunity: int | None,
) -> tuple[int | None, TaskResourceType | None]:
    """Map friendly --contact/--project/--opportunity options to (resource_id, resource_type).

    Raises BadParameter if more than one is provided.
    Returns (None, None) if none are provided.
    """
    result: tuple[int | None, TaskResourceType | None] = (None, None)
    for id_, rtype in (
        (contact, TaskResourceType.CONTACT),
        (project, TaskResourceType.PROJECT),
        (opportunity, TaskResourceType.OPPORTUNITY),
    ):
        if id_ is not None:
            if result[0] is not None:
                raise typer.BadParameter("Provide only one of --contact, --project, or --opportunity.")
            result = (id_, rtype)
    return result


async def resolve_category_id(
    client: WealthboxClient, category_type: CategoryType, value: str
) -> int:
    """Resolve a category name or numeric string to an integer ID.

    If `value` is purely digits, returns int(value) without an API call.
    Otherwise fetches all categories of the given type and case-insensitively
    matches `name`. Raises typer.BadParameter on miss with available names.
    """
    if value.isdigit():
        return int(value)
    data = await client.list_all_categories(category_type)
    items = data.get(category_type.value, [])
    target = value.strip().casefold()
    for item in items:
        if str(item.get("name", "")).casefold() == target:
            return int(item["id"])
    available = sorted(str(i["name"]) for i in items if i.get("name"))
    label = category_type.value.replace("_", " ")
    if available:
        raise typer.BadParameter(
            f"Unknown {label} value '{value}'. Available: {', '.join(available)}"
        )
    raise typer.BadParameter(f"No {label} configured in this workspace.")


def _match_contact_role(roles: list[dict[str, Any]], token: str) -> dict[str, Any]:
    """Find a contact role by numeric id or case-insensitive name."""
    if token.isdigit():
        rid = int(token)
        for r in roles:
            if int(r.get("id", 0)) == rid:
                return r
        raise typer.BadParameter(f"No contact role with id {rid} in this workspace.")
    target = token.casefold()
    for r in roles:
        if str(r.get("name", "")).casefold() == target:
            return r
    available = sorted(str(r["name"]) for r in roles if r.get("name"))
    raise typer.BadParameter(
        f"Unknown contact role '{token}'. Available: {', '.join(available) or '(none configured)'}"
    )


def _role_option_user(option: dict[str, Any]) -> dict[str, Any]:
    return option.get("assigned_to") or {}


def _match_role_option(role: dict[str, Any], token: str) -> int:
    """Resolve a user (numeric id, exact name, or unique substring) to a role-option id."""
    options = role.get("available_options", []) or []
    role_name = role.get("name", "role")
    if token.isdigit():
        uid = int(token)
        for opt in options:
            if int(_role_option_user(opt).get("id", 0)) == uid:
                return int(opt["id"])
        raise typer.BadParameter(f"No user with id {uid} is available for role '{role_name}'.")
    target = token.casefold()
    exact = [o for o in options if str(_role_option_user(o).get("name", "")).casefold() == target]
    matches = exact or [
        o for o in options if target in str(_role_option_user(o).get("name", "")).casefold()
    ]
    if len(matches) == 1:
        return int(matches[0]["id"])
    if not matches:
        names = sorted(str(_role_option_user(o).get("name", "")) for o in options)
        raise typer.BadParameter(
            f"No user matching '{token}' for role '{role_name}'. Available: {', '.join(names)}"
        )
    cand = sorted(str(_role_option_user(o).get("name", "")) for o in matches)
    raise typer.BadParameter(
        f"'{token}' is ambiguous for role '{role_name}': matches {', '.join(cand)}. Be more specific."
    )


async def resolve_contact_roles(client: WealthboxClient, specs: list[str]) -> list[dict[str, int]]:
    """Resolve ``Role:User`` specs to ``[{"id": role_id, "value": option_id}]`` entries.

    Role may be a contact-role name (case-insensitive) or numeric id. User may be a
    user name (case-insensitive; exact preferred, else unique substring) or numeric
    user id. Both are resolved against ``wbox contacts categories contact-roles`` —
    the option id (``available_options[].id``), not the user id, is the value the
    Wealthbox API stores.
    """
    data = await client.list_all_categories(CategoryType.CONTACT_ROLES)
    roles = data.get("contact_roles", []) or []
    resolved: list[dict[str, int]] = []
    for spec in specs:
        role_token, sep, user_token = spec.partition(":")
        role_token, user_token = role_token.strip(), user_token.strip()
        if not sep or not role_token or not user_token:
            raise typer.BadParameter(
                f"--advisor-role expects 'Role:User' (e.g. 'Associate Advisor:Greg Hyde'); got '{spec}'."
            )
        role = _match_contact_role(roles, role_token)
        resolved.append({"id": int(role["id"]), "value": _match_role_option(role, user_token)})
    return resolved


def parse_more_fields(more_fields: str, reserved: set[str]) -> dict[str, Any]:
    """Parse --more-fields JSON and validate against reserved keys.

    Raises BadParameter if the value is not valid JSON, not an object, or collides with
    a reserved key that has an explicit CLI flag.
    """
    try:
        extra = json.loads(more_fields)
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"--more-fields must be valid JSON: {e.msg}") from e
    if not isinstance(extra, dict):
        raise typer.BadParameter("--more-fields must be a JSON object (e.g. {...}), not a list or string.")
    collision = reserved.intersection(extra.keys())
    if collision:
        raise typer.BadParameter(f"--more-fields cannot include {sorted(collision)}; use explicit CLI args instead.")
    return extra


def parse_custom_fields(specs: list[str]) -> list[tuple[str, str]]:
    """Split repeatable ``--custom-field NAME=VALUE`` specs into pairs.

    The value is everything after the first ``=``, so values containing ``=``
    need no escaping. Name resolution happens in :func:`resolve_custom_fields`,
    which needs a client.
    """
    pairs: list[tuple[str, str]] = []
    for spec in specs:
        key, sep, value = spec.partition("=")
        key = key.strip()
        if not sep or not key:
            raise typer.BadParameter(
                f"--custom-field expects 'NAME=VALUE' (e.g. 'Risk Tolerance=High'); got '{spec}'."
            )
        pairs.append((key, value))
    return pairs


async def resolve_custom_fields(
    client: WealthboxClient, document_type: DocumentType, specs: list[str]
) -> list[CustomFieldValue] | None:
    """Resolve ``NAME=VALUE`` specs to ``[{"id": field_id, "value": ...}]``.

    Wealthbox only honours custom fields keyed by numeric ``id``; a payload
    keyed by ``name`` is accepted with a 200 and silently discarded. So a
    non-numeric name is looked up (case-insensitively) against
    ``GET /categories/custom_fields?document_type=<type>`` and an unknown name
    is a hard error listing what the workspace actually defines — far better
    than a write that reports success and changes nothing.

    Returns ``None`` for an empty spec list so callers can drop the key.
    """
    pairs = parse_custom_fields(specs)
    if not pairs:
        return None

    resolved: list[CustomFieldValue] = []
    by_name: dict[str, int] | None = None
    available: list[str] = []
    for key, value in pairs:
        if key.isdigit():
            resolved.append(CustomFieldValue(id=int(key), value=value))
            continue
        if by_name is None:
            data = await client.list_all_categories(
                CategoryType.CUSTOM_FIELDS, CategoryListQuery(document_type=document_type)
            )
            items = data.get("custom_fields", [])
            by_name = {str(i["name"]).casefold(): int(i["id"]) for i in items if i.get("name")}
            available = sorted(str(i["name"]) for i in items if i.get("name"))
        field_id = by_name.get(key.casefold())
        if field_id is None:
            hint = ", ".join(available) if available else "(none configured for this record type)"
            raise typer.BadParameter(
                f"Unknown custom field '{key}' for {document_type.value}. Available: {hint}"
            )
        resolved.append(CustomFieldValue(id=field_id, value=value))
    return resolved
