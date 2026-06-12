from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_PROJECT_RESPONSE = {
    "id": 7,
    "name": "Onboarding Project",
    "description": "New client onboarding",
    "organizer": {"id": 42, "name": "Jane Advisor"},
    "updated_at": "2026-06-01T10:00:00Z",
}


@respx.mock
def test_update_project_name(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/projects/7").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "update", "7", "--name", "Revised Onboarding"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["name"] == "Revised Onboarding"
    # Partial update: other fields must be absent
    assert "description" not in sent
    assert "organizer" not in sent
    assert "visible_to" not in sent


@respx.mock
def test_update_project_description(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/projects/7").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "update", "7", "--description", "Updated description"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["description"] == "Updated description"
    assert "name" not in sent


@respx.mock
def test_update_project_organizer(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/projects/7").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "update", "7", "--organizer", "42"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["organizer"] == 42
    assert "name" not in sent
    assert "description" not in sent


@respx.mock
def test_update_project_visible_to(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/projects/7").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "update", "7", "--visible-to", "owner"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["visible_to"] == "owner"
    assert "name" not in sent


@respx.mock
def test_update_project_name_only_payload_exact(runner) -> None:
    """Only the supplied field is sent — no extra keys from defaults."""
    route = respx.put("https://api.crmworkspace.com/v1/projects/7").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "update", "7", "--name", "Exact name only"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent == {"name": "Exact name only"}


@respx.mock
def test_update_project_multiple_fields(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/projects/7").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["projects", "update", "7", "--name", "Multi-field update", "--description", "New desc"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["name"] == "Multi-field update"
    assert sent["description"] == "New desc"
    assert "organizer" not in sent
    assert "visible_to" not in sent


@respx.mock
def test_update_project_uses_put_method(runner) -> None:
    """Verify that the update command sends a PUT (not PATCH or POST)."""
    route = respx.put("https://api.crmworkspace.com/v1/projects/7").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "update", "7", "--name", "Check method"])
    assert result.exit_code == 0
    assert route.calls[0].request.method == "PUT"


def test_update_project_no_fields_raises(runner) -> None:
    """ProjectUpdateInput extends RequireAnyFieldModel — empty payload is rejected."""
    result = runner.invoke(app, ["projects", "update", "7"])
    assert result.exit_code != 0
