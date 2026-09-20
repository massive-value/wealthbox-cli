"""Subtasks arrive in the normal task list carrying a `parent {id, type}`
object; verbose output must not hide it."""
from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app

_SUBTASK = {
    "id": 77,
    "name": "Gather statements",
    "due_date": "2026-03-20",
    "frame": None,
    "complete": False,
    "category": None,
    "parent": {"id": 25299889, "type": "WorkflowStep"},
    "due_based_on": "default",
    "due_later": "Same day at 6:00 AM",
}


@respx.mock
def test_verbose_list_shows_parent(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json={"tasks": [_SUBTASK], "meta": {"total_count": 1}})
    )
    result = runner.invoke(app, ["tasks", "list", "--type", "subtasks", "--verbose"])
    assert result.exit_code == 0
    assert '"parent"' in result.stdout
    assert '"type": "WorkflowStep"' in result.stdout
    assert '"due_later"' in result.stdout


@respx.mock
def test_default_list_stays_slim(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json={"tasks": [_SUBTASK], "meta": {"total_count": 1}})
    )
    result = runner.invoke(app, ["tasks", "list", "--type", "subtasks"])
    assert result.exit_code == 0
    assert '"parent"' not in result.stdout
