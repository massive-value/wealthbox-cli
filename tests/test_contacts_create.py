from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_CONTACT_RESPONSE = {"id": 1, "name": "John Doe", "type": "Person"}


# --- type argument: required, case-insensitive ---

def test_add_contact_missing_type_raises(runner) -> None:
    result = runner.invoke(app, ["contacts", "add", "--first-name", "John"])
    assert result.exit_code != 0


def test_add_contact_invalid_type_raises(runner) -> None:
    result = runner.invoke(app, ["contacts", "add", "Alien", "--first-name", "John"])
    assert result.exit_code != 0


@respx.mock
def test_add_contact_type_case_insensitive(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "add", "person", "--first-name", "John"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Person"


@respx.mock
def test_add_contact_type_uppercase(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "add", "HOUSEHOLD", "--first-name", "Smith"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Household"


# --- flags path ---

@respx.mock
def test_add_contact_flags_path(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["contacts", "add", "Person", "--first-name", "John", "--last-name", "Doe", "--contact-type", "Client"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["type"] == "Person"
    assert sent["first_name"] == "John"
    assert sent["last_name"] == "Doe"
    assert sent["contact_type"] == "Client"


@respx.mock
def test_add_contact_active_flag(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "add", "Person", "--first-name", "John", "--active"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Active"


@respx.mock
def test_add_contact_inactive_flag(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "add", "Person", "--first-name", "John", "--inactive"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Inactive"


@respx.mock
def test_add_contact_no_status_flag_omits_status(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "add", "Person", "--first-name", "John"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert "status" not in sent


@respx.mock
def test_add_contact_with_email_no_type(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["contacts", "add", "Person", "--first-name", "John", "--email", "john@example.com"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["email_addresses"] == [{"address": "john@example.com", "principal": True}]
    assert "kind" not in sent["email_addresses"][0]


@respx.mock
def test_add_contact_with_email_and_type(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["contacts", "add", "Person", "--first-name", "John", "--email", "john@example.com", "--email-type", "Personal"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["email_addresses"] == [{"address": "john@example.com", "kind": "Personal", "principal": True}]


@respx.mock
def test_add_contact_with_phone_no_type(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["contacts", "add", "Person", "--first-name", "John", "--phone", "555-1234"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["phone_numbers"] == [{"address": "555-1234", "principal": True}]
    assert "kind" not in sent["phone_numbers"][0]


@respx.mock
def test_add_contact_with_phone_and_type(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["contacts", "add", "Person", "--first-name", "John", "--phone", "555-1234", "--phone-type", "Mobile"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["phone_numbers"] == [{"address": "555-1234", "kind": "Mobile", "principal": True}]


# --- --json path ---

@respx.mock
def test_add_contact_json_path(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    payload = json.dumps({"type": "Person", "first_name": "Jane", "last_name": "Doe"})
    result = runner.invoke(app, ["contacts", "add", "--json", payload])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["first_name"] == "Jane"


def test_add_contact_json_missing_type_raises(runner) -> None:
    payload = json.dumps({"first_name": "Jane", "last_name": "Doe"})
    result = runner.invoke(app, ["contacts", "add", "--json", payload])
    assert result.exit_code != 0
