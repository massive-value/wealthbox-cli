"""Tests for contact-role assignment: the {id, value} model shape and the
--advisor-role flag that resolves 'Role:User' specs to role+option ids."""
from __future__ import annotations

import json

import httpx
import pytest
import respx
from pydantic import ValidationError

from wealthbox_tools.cli.main import app
from wealthbox_tools.models import ContactCreateInput, ContactUpdateInput

_CONTACTS_URL = "https://api.crmworkspace.com/v1/contacts"
_ROLES_URL = "https://api.crmworkspace.com/v1/categories/contact_roles"
_CONTACT_RESPONSE = {"id": 1, "name": "John Doe", "type": "Person"}

# Mirrors the live `categories contact_roles` shape: each role carries
# available_options whose `id` (NOT the user id) is what the API stores.
_ROLES_RESPONSE = {
    "contact_roles": [
        {
            "id": 1338,
            "name": "Associate Advisor",
            "available_options": [
                {"id": 3465, "assigned_to": {"id": 152760, "type": "User", "name": "Kadin Bullock"}},
                {"id": 4226, "assigned_to": {"id": 154372, "type": "User", "name": "Greg Hyde"}},
            ],
        },
        {
            "id": 2727,
            "name": "Partner",
            "available_options": [
                {"id": 7651, "assigned_to": {"id": 154372, "type": "User", "name": "Greg Hyde"}},
            ],
        },
    ]
}


# ---------------------------------------------------------------------------
# model: the write shape is {id, value}, both required positive ints
# ---------------------------------------------------------------------------

def test_model_accepts_id_value() -> None:
    m = ContactCreateInput(type="Person", first_name="X", contact_roles=[{"id": 1338, "value": 3465}])
    assert m.model_dump(exclude_none=True)["contact_roles"] == [{"id": 1338, "value": 3465}]


def test_model_update_accepts_id_value() -> None:
    u = ContactUpdateInput(contact_roles=[{"id": 2727, "value": 4226}])
    assert u.model_dump(exclude_unset=True)["contact_roles"] == [{"id": 2727, "value": 4226}]


@pytest.mark.parametrize(
    "bad",
    [
        {"id": 1338},  # missing value
        {"value": 3465},  # missing id
        {"id": 1338, "value": 3465, "type": "User"},  # stale read-shape extra
        {"id": 1338, "value": 0},  # value must be >= 1
    ],
)
def test_model_rejects_bad_role_shapes(bad: dict) -> None:  # type: ignore[type-arg]
    with pytest.raises(ValidationError):
        ContactCreateInput(type="Person", contact_roles=[bad])


# ---------------------------------------------------------------------------
# --advisor-role on create
# ---------------------------------------------------------------------------

@respx.mock
def test_add_person_advisor_role_by_name(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.post(_CONTACTS_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John",
         "--advisor-role", "Associate Advisor:Kadin Bullock"],
    )
    assert result.exit_code == 0, result.output
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_roles"] == [{"id": 1338, "value": 3465}]


@respx.mock
def test_add_person_advisor_role_by_user_id(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.post(_CONTACTS_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John",
         "--advisor-role", "Associate Advisor:154372"],
    )
    assert result.exit_code == 0, result.output
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_roles"] == [{"id": 1338, "value": 4226}]


@respx.mock
def test_add_person_advisor_role_substring_match(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.post(_CONTACTS_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John", "--advisor-role", "Partner:Greg"],
    )
    assert result.exit_code == 0, result.output
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_roles"] == [{"id": 2727, "value": 7651}]


@respx.mock
def test_add_person_multiple_advisor_roles(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.post(_CONTACTS_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John",
         "--advisor-role", "Associate Advisor:Kadin Bullock",
         "--advisor-role", "Partner:Greg Hyde"],
    )
    assert result.exit_code == 0, result.output
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_roles"] == [{"id": 1338, "value": 3465}, {"id": 2727, "value": 7651}]


@respx.mock
def test_add_household_advisor_role(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.post(_CONTACTS_URL).mock(
        return_value=httpx.Response(200, json={"id": 2, "name": "The Smiths", "type": "Household"})
    )
    result = runner.invoke(
        app,
        ["contacts", "add", "household", "--name", "The Smiths",
         "--advisor-role", "Associate Advisor:Greg Hyde"],
    )
    assert result.exit_code == 0, result.output
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_roles"] == [{"id": 1338, "value": 4226}]


@respx.mock
def test_add_org_advisor_role(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.post(_CONTACTS_URL).mock(
        return_value=httpx.Response(200, json={"id": 3, "name": "Acme", "type": "Organization"})
    )
    result = runner.invoke(
        app,
        ["contacts", "add", "org", "--name", "Acme", "--advisor-role", "Partner:Greg Hyde"],
    )
    assert result.exit_code == 0, result.output
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_roles"] == [{"id": 2727, "value": 7651}]


# ---------------------------------------------------------------------------
# --advisor-role error handling
# ---------------------------------------------------------------------------

@respx.mock
def test_advisor_role_unknown_role_fails_without_post(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.post(_CONTACTS_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John", "--advisor-role", "Bogus Role:Greg Hyde"],
    )
    assert result.exit_code != 0
    assert not route.called


@respx.mock
def test_advisor_role_unknown_user_fails(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    respx.post(_CONTACTS_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John",
         "--advisor-role", "Associate Advisor:Nobody"],
    )
    assert result.exit_code != 0


def test_advisor_role_bad_format_fails(runner) -> None:
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John", "--advisor-role", "no-colon-here"],
    )
    assert result.exit_code != 0


def test_advisor_role_collides_with_more_fields(runner) -> None:
    extra = json.dumps({"contact_roles": [{"id": 1338, "value": 3465}]})
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John",
         "--advisor-role", "Associate Advisor:Kadin Bullock", "--more-fields", extra],
    )
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --advisor-role on update
# ---------------------------------------------------------------------------

@respx.mock
def test_update_advisor_role(runner) -> None:
    respx.get(_ROLES_URL).mock(return_value=httpx.Response(200, json=_ROLES_RESPONSE))
    route = respx.put("https://api.crmworkspace.com/v1/contacts/10").mock(
        return_value=httpx.Response(200, json={"id": 10, "name": "John Doe", "type": "Person"})
    )
    result = runner.invoke(
        app,
        ["contacts", "update", "10", "--advisor-role", "Associate Advisor:Kadin Bullock"],
    )
    assert result.exit_code == 0, result.output
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_roles"] == [{"id": 1338, "value": 3465}]


def test_update_advisor_role_collides_with_json(runner) -> None:
    payload = json.dumps({"first_name": "Jon"})
    result = runner.invoke(
        app,
        ["contacts", "update", "10", "--json", payload,
         "--advisor-role", "Associate Advisor:Kadin Bullock"],
    )
    assert result.exit_code != 0
