from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_CONTACT_RESPONSE = {"id": 1, "name": "John Doe", "type": "Person"}
_API_URL = "https://api.crmworkspace.com/v1/contacts"


# ---------------------------------------------------------------------------
# add person
# ---------------------------------------------------------------------------

@respx.mock
def test_add_person_happy_path(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John", "--last-name", "Doe"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Person"
    assert sent["first_name"] == "John"
    assert sent["last_name"] == "Doe"


@respx.mock
def test_add_person_type_hardcoded(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "Jane"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Person"


@respx.mock
def test_add_person_active_flag(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John", "--active"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Active"


@respx.mock
def test_add_person_inactive_flag(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John", "--inactive"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Inactive"


@respx.mock
def test_add_person_no_status_omits_field(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert "status" not in sent


@respx.mock
def test_add_person_person_specific_flags(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        [
            "contacts", "add", "person",
            "--first-name", "John",
            "--prefix", "Dr.",
            "--suffix", "Jr.",
            "--nickname", "Johnny",
            "--gender", "Male",
            "--marital-status", "Married",
            "--birth-date", "1980-01-15",
            "--anniversary", "2005-06-10",
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["prefix"] == "Dr."
    assert sent["suffix"] == "Jr."
    assert sent["nickname"] == "Johnny"
    assert sent["gender"] == "Male"
    assert sent["marital_status"] == "Married"
    assert sent["birth_date"] == "1980-01-15"
    assert sent["anniversary"] == "2005-06-10"


@respx.mock
def test_add_person_email_no_type(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John", "--email", "john@example.com"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["email_addresses"] == [{"address": "john@example.com", "principal": True}]
    assert "kind" not in sent["email_addresses"][0]


@respx.mock
def test_add_person_email_with_type(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John", "--email", "john@example.com", "--email-type", "Personal"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["email_addresses"] == [{"address": "john@example.com", "kind": "Personal", "principal": True}]


@respx.mock
def test_add_person_phone_no_type(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John", "--phone", "555-1234"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["phone_numbers"] == [{"address": "555-1234", "principal": True}]
    assert "kind" not in sent["phone_numbers"][0]


@respx.mock
def test_add_person_phone_with_type(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "John", "--phone", "555-1234", "--phone-type", "Mobile"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["phone_numbers"] == [{"address": "555-1234", "kind": "Mobile", "principal": True}]


@respx.mock
def test_add_person_more_fields_merges(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json=_CONTACT_RESPONSE))
    extra = json.dumps({"background_information": "VIP client", "client_since": "2020-01-01"})
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John", "--more-fields", extra])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["background_information"] == "VIP client"
    assert sent["client_since"] == "2020-01-01"
    assert sent["first_name"] == "John"


def test_add_person_more_fields_reserved_key_raises(runner) -> None:
    extra = json.dumps({"first_name": "Oops"})
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John", "--more-fields", extra])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# add household
# ---------------------------------------------------------------------------

@respx.mock
def test_add_household_happy_path(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 2, "name": "The Smiths", "type": "Household"}))
    result = runner.invoke(app, ["contacts", "add", "household", "--name", "The Smiths"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Household"
    assert sent["name"] == "The Smiths"


def test_add_household_missing_name_raises(runner) -> None:
    result = runner.invoke(app, ["contacts", "add", "household"])
    assert result.exit_code != 0


@respx.mock
def test_add_household_type_hardcoded(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 2, "name": "The Smiths", "type": "Household"}))
    result = runner.invoke(app, ["contacts", "add", "household", "--name", "The Smiths"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Household"


@respx.mock
def test_add_household_active_flag(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 2, "name": "The Smiths", "type": "Household"}))
    result = runner.invoke(app, ["contacts", "add", "household", "--name", "The Smiths", "--active"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Active"


@respx.mock
def test_add_household_email_with_type(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 2, "name": "The Smiths", "type": "Household"}))
    result = runner.invoke(
        app,
        ["contacts", "add", "household", "--name", "The Smiths", "--email", "smiths@example.com", "--email-type", "Work"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["email_addresses"] == [{"address": "smiths@example.com", "kind": "Work", "principal": True}]


@respx.mock
def test_add_household_more_fields_merges(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 2, "name": "The Smiths", "type": "Household"}))
    extra = json.dumps({"background_information": "High net worth"})
    result = runner.invoke(app, ["contacts", "add", "household", "--name", "The Smiths", "--more-fields", extra])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["background_information"] == "High net worth"


def test_add_household_more_fields_reserved_key_raises(runner) -> None:
    extra = json.dumps({"name": "Oops"})
    result = runner.invoke(app, ["contacts", "add", "household", "--name", "The Smiths", "--more-fields", extra])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# add org
# ---------------------------------------------------------------------------

@respx.mock
def test_add_org_happy_path(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 3, "name": "Acme Co.", "type": "Organization"}))
    result = runner.invoke(app, ["contacts", "add", "org", "--name", "Acme Co."])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Organization"
    assert sent["name"] == "Acme Co."


def test_add_org_missing_name_raises(runner) -> None:
    result = runner.invoke(app, ["contacts", "add", "org"])
    assert result.exit_code != 0


@respx.mock
def test_add_org_type_hardcoded(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 3, "name": "Acme Co.", "type": "Organization"}))
    result = runner.invoke(app, ["contacts", "add", "org", "--name", "Acme Co."])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Organization"


@respx.mock
def test_add_org_phone_with_type(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 3, "name": "Acme Co.", "type": "Organization"}))
    result = runner.invoke(
        app,
        ["contacts", "add", "org", "--name", "Acme Co.", "--phone", "800-555-0000", "--phone-type", "Work"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["phone_numbers"] == [{"address": "800-555-0000", "kind": "Work", "principal": True}]


@respx.mock
def test_add_org_more_fields_merges(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 3, "name": "Acme Co.", "type": "Organization"}))
    extra = json.dumps({"background_information": "Fortune 500"})
    result = runner.invoke(app, ["contacts", "add", "org", "--name", "Acme Co.", "--more-fields", extra])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["background_information"] == "Fortune 500"


def test_add_org_more_fields_reserved_key_raises(runner) -> None:
    extra = json.dumps({"name": "Oops"})
    result = runner.invoke(app, ["contacts", "add", "org", "--name", "Acme Co.", "--more-fields", extra])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# add trust
# ---------------------------------------------------------------------------

@respx.mock
def test_add_trust_happy_path(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 4, "name": "Conglomerate Trust", "type": "Trust"}))
    result = runner.invoke(app, ["contacts", "add", "trust", "--name", "Conglomerate Trust"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Trust"
    assert sent["name"] == "Conglomerate Trust"


def test_add_trust_missing_name_raises(runner) -> None:
    result = runner.invoke(app, ["contacts", "add", "trust"])
    assert result.exit_code != 0


@respx.mock
def test_add_trust_type_hardcoded(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 4, "name": "Conglomerate Trust", "type": "Trust"}))
    result = runner.invoke(app, ["contacts", "add", "trust", "--name", "Conglomerate Trust"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Trust"


@respx.mock
def test_add_trust_inactive_flag(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 4, "name": "Conglomerate Trust", "type": "Trust"}))
    result = runner.invoke(app, ["contacts", "add", "trust", "--name", "Conglomerate Trust", "--inactive"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Inactive"


@respx.mock
def test_add_trust_email_no_type(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 4, "name": "Conglomerate Trust", "type": "Trust"}))
    result = runner.invoke(
        app,
        ["contacts", "add", "trust", "--name", "Conglomerate Trust", "--email", "trust@example.com"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["email_addresses"] == [{"address": "trust@example.com", "principal": True}]


@respx.mock
def test_add_trust_more_fields_merges(runner) -> None:
    route = respx.post(_API_URL).mock(return_value=httpx.Response(200, json={"id": 4, "name": "Conglomerate Trust", "type": "Trust"}))
    extra = json.dumps({"important_information": "Irrevocable"})
    result = runner.invoke(app, ["contacts", "add", "trust", "--name", "Conglomerate Trust", "--more-fields", extra])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["important_information"] == "Irrevocable"


def test_add_trust_more_fields_reserved_key_raises(runner) -> None:
    extra = json.dumps({"type": "Oops"})
    result = runner.invoke(app, ["contacts", "add", "trust", "--name", "Conglomerate Trust", "--more-fields", extra])
    assert result.exit_code != 0
