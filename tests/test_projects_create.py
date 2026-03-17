from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_PROJECT_RESPONSE = {
    "id": 10,
    "name": "Onboarding",
    "description": "New client onboarding",
    "organizer": None,
    "updated_at": "2026-03-17T00:00:00Z",
}


@respx.mock
def test_add_project_required_fields(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/projects").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(
        app, ["projects", "add", "Onboarding", "--description", "New client onboarding"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["name"] == "Onboarding"
    assert sent["description"] == "New client onboarding"
    assert "organizer" not in sent


@respx.mock
def test_add_project_with_organizer(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/projects").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["projects", "add", "Onboarding",
         "--description", "New client onboarding",
         "--organizer", "99"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["organizer"] == 99


@respx.mock
def test_add_project_with_more_fields(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/projects").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["projects", "add", "Onboarding",
         "--description", "New client onboarding",
         "--more-fields", '{"custom_fields": [{"id": 5, "value": "priority"}]}'],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["custom_fields"] == [{"id": 5, "value": "priority"}]


def test_add_project_missing_description(runner) -> None:
    result = runner.invoke(app, ["projects", "add", "Onboarding"])
    assert result.exit_code != 0


@respx.mock
def test_update_project_partial(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/projects/10").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "update", "10", "--name", "Renamed Project"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["name"] == "Renamed Project"
    assert "description" not in sent


def test_update_project_empty_raises(runner) -> None:
    result = runner.invoke(app, ["projects", "update", "10"])
    assert result.exit_code != 0
