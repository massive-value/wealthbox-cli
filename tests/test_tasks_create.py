from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_TASK_RESPONSE = {"id": 1, "name": "Send proposal", "due_date": "2026-03-20", "frame": None}


@respx.mock
def test_add_task_with_due_date(runner) -> None:
    respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(
        app, ["tasks", "add", "Send proposal", "--due-date", "2026-03-20T09:00:00-07:00"]
    )
    assert result.exit_code == 0


@respx.mock
def test_add_task_with_frame(runner) -> None:
    respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "add", "Follow up", "--frame", "tomorrow"])
    assert result.exit_code == 0


@respx.mock
def test_add_task_with_priority(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["tasks", "add", "Send proposal", "--due-date", "2026-03-20T09:00:00-07:00", "--priority", "High"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["priority"] == "High"


@respx.mock
def test_add_task_with_contact(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["tasks", "add", "Send proposal", "--due-date", "2026-03-20T09:00:00-07:00", "--contact", "12345"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 12345, "type": "Contact"}]


@respx.mock
def test_add_task_more_fields_regression(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Send proposal",
            "--due-date", "2026-03-20T09:00:00-07:00",
            "--more-fields", '{"assigned_to_team": 456}',
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["assigned_to_team"] == 456


def test_add_task_priority_in_more_fields_raises(runner) -> None:
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Send proposal",
            "--due-date", "2026-03-20T09:00:00-07:00",
            "--more-fields", '{"priority": "High"}',
        ],
    )
    assert result.exit_code != 0
    assert "priority" in result.output.lower() or "priority" in (result.stderr or "").lower()


def test_add_task_category_in_more_fields_raises(runner) -> None:
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Send proposal",
            "--due-date", "2026-03-20T09:00:00-07:00",
            "--more-fields", '{"category": 99}',
        ],
    )
    assert result.exit_code != 0
    assert "category" in result.output.lower() or "category" in (result.stderr or "").lower()


@respx.mock
def test_add_task_with_category_numeric(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    # No mock for /categories — if the CLI calls it, respx will raise.
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Send proposal",
            "--due-date", "2026-03-20T09:00:00-07:00",
            "--category", "173277",
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["category"] == 173277


@respx.mock
def test_add_task_with_category_name_resolves_to_id(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/categories/task_categories").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_categories": [
                    {"id": 100, "name": "Phone"},
                    {"id": 173277, "name": "Follow-up"},
                ],
                "meta": {"total_count": 2},
            },
        )
    )
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Send proposal",
            "--due-date", "2026-03-20T09:00:00-07:00",
            "--category", "follow-up",  # case-insensitive match
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["category"] == 173277


@respx.mock
def test_add_task_with_unknown_category_errors(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/categories/task_categories").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_categories": [
                    {"id": 100, "name": "Phone"},
                    {"id": 173277, "name": "Follow-up"},
                ],
                "meta": {"total_count": 2},
            },
        )
    )
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Send proposal",
            "--due-date", "2026-03-20T09:00:00-07:00",
            "--category", "Bogus",
        ],
    )
    assert result.exit_code != 0
    out = result.output + (result.stderr or "")
    assert "Bogus" in out
    assert "Phone" in out and "Follow-up" in out


@respx.mock
def test_add_task_with_description(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Send proposal",
            "--due-date", "2026-03-20T09:00:00-07:00",
            "--description", "Send the Q2 proposal deck.",
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["description"] == "Send the Q2 proposal deck."


def test_add_task_missing_due_date_and_frame(runner) -> None:
    result = runner.invoke(app, ["tasks", "add", "Send proposal"])
    assert result.exit_code != 0


def test_add_task_both_due_date_and_frame(runner) -> None:
    result = runner.invoke(
        app,
        ["tasks", "add", "Send proposal", "--due-date", "2026-03-20T09:00:00-07:00", "--frame", "today"],
    )
    assert result.exit_code != 0
