from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_EVENT_RESPONSE = {
    "id": 1,
    "title": "Annual Review",
    "starts_at": "2026-04-01T10:00:00-07:00",
    "ends_at": "2026-04-01T11:00:00-07:00",
    "state": "confirmed",
}

_STARTS = "2026-04-01T10:00:00-07:00"
_ENDS = "2026-04-01T11:00:00-07:00"


@respx.mock
def test_add_event_required_only(runner) -> None:
    respx.post("https://api.crmworkspace.com/v1/events").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(
        app, ["events", "add", "Annual Review", "--starts-at", _STARTS, "--ends-at", _ENDS]
    )
    assert result.exit_code == 0


@respx.mock
def test_add_event_with_state(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/events").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["events", "add", "Annual Review", "--starts-at", _STARTS, "--ends-at", _ENDS, "--state", "confirmed"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["state"] == "confirmed"


@respx.mock
def test_add_event_with_contact(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/events").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["events", "add", "Annual Review", "--starts-at", _STARTS, "--ends-at", _ENDS, "--contact", "123"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 123, "type": "Contact"}]


@respx.mock
def test_add_event_with_location(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/events").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["events", "add", "Annual Review", "--starts-at", _STARTS, "--ends-at", _ENDS, "--location", "Office"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["location"] == "Office"


def test_add_event_missing_starts_at(runner) -> None:
    result = runner.invoke(app, ["events", "add", "Annual Review", "--ends-at", _ENDS])
    assert result.exit_code != 0


def test_add_event_missing_ends_at(runner) -> None:
    result = runner.invoke(app, ["events", "add", "Annual Review", "--starts-at", _STARTS])
    assert result.exit_code != 0
