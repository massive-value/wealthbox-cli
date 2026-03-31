from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_TASK_RESPONSE = {"id": 5, "name": "Send proposal", "due_date": "2026-03-20", "frame": None}


@respx.mock
def test_update_task_name(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--name", "Send revised proposal"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["name"] == "Send revised proposal"
    assert "due_date" not in sent


@respx.mock
def test_update_task_priority(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--priority", "High"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["priority"] == "High"


@respx.mock
def test_update_task_complete(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--complete"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["complete"] is True


@respx.mock
def test_update_task_no_complete(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--no-complete"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["complete"] is False


@respx.mock
def test_update_task_with_contact(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--contact", "999"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 999, "type": "Contact"}]


@respx.mock
def test_update_task_due_date(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(
        app, ["tasks", "update", "5", "--due-date", "2026-04-01T09:00:00-07:00"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["due_date"] == "2026-04-01T09:00:00-07:00"


def test_update_task_no_fields_raises(runner) -> None:
    result = runner.invoke(app, ["tasks", "update", "5"])
    assert result.exit_code != 0


@respx.mock
def test_update_task_name_only_no_date_required(runner) -> None:
    """Updating just the name should succeed — no due_date or frame needed."""
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--name", "New name"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent == {"name": "New name"}
