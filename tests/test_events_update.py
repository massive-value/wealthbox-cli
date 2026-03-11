from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_EVENT_RESPONSE = {
    "id": 3,
    "title": "Annual Review",
    "starts_at": "2026-04-01 10:00 AM -0700",
    "ends_at": "2026-04-01 11:00 AM -0700",
    "state": "confirmed",
}


@respx.mock
def test_update_event_title(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/events/3").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(app, ["events", "update", "3", "--title", "Q2 Review"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["title"] == "Q2 Review"
    assert "starts_at" not in sent


@respx.mock
def test_update_event_state(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/events/3").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(app, ["events", "update", "3", "--state", "cancelled"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["state"] == "cancelled"


@respx.mock
def test_update_event_location(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/events/3").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(app, ["events", "update", "3", "--location", "Conference Room B"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["location"] == "Conference Room B"


@respx.mock
def test_update_event_all_day(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/events/3").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(app, ["events", "update", "3", "--all-day"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["all_day"] is True


@respx.mock
def test_update_event_with_contact(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/events/3").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(app, ["events", "update", "3", "--contact", "42"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 42, "type": "Contact"}]


@respx.mock
def test_update_event_reschedule(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/events/3").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    result = runner.invoke(
        app,
        [
            "events", "update", "3",
            "--starts-at", "2026-05-01 10:00 AM -0700",
            "--ends-at", "2026-05-01 11:00 AM -0700",
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["starts_at"] == "2026-05-01 10:00 AM -0700"
    assert sent["ends_at"] == "2026-05-01 11:00 AM -0700"


def test_update_event_no_fields_raises(runner) -> None:
    result = runner.invoke(app, ["events", "update", "3"])
    assert result.exit_code != 0
