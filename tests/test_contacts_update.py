from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_CONTACT_RESPONSE = {"id": 10, "name": "John Doe", "type": "Person"}


@respx.mock
def test_update_contact_name(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/contacts/10").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(
        app, ["contacts", "update", "10", "--first-name", "Jonathan"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["first_name"] == "Jonathan"
    assert "last_name" not in sent


@respx.mock
def test_update_contact_multiple_fields(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/contacts/10").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(
        app,
        [
            "contacts", "update", "10",
            "--contact-type", "Client",
            "--active",
            "--assigned-to", "7",
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["contact_type"] == "Client"
    assert sent["status"] == "Active"
    assert sent["assigned_to"] == 7


@respx.mock
def test_update_contact_json_path(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/contacts/10").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    payload = json.dumps({"last_name": "Smith", "job_title": "CFO"})
    result = runner.invoke(app, ["contacts", "update", "10", "--json", payload])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["last_name"] == "Smith"
    assert sent["job_title"] == "CFO"


@respx.mock
def test_update_contact_active_flag(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/contacts/10").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "update", "10", "--active"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Active"


@respx.mock
def test_update_contact_inactive_flag(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/contacts/10").mock(
        return_value=httpx.Response(200, json=_CONTACT_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "update", "10", "--inactive"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["status"] == "Inactive"


def test_update_contact_no_fields_raises(runner) -> None:
    result = runner.invoke(app, ["contacts", "update", "10"])
    assert result.exit_code != 0
