"""`--status` on tasks and workflows: the call count and params per value.

Wealthbox's list defaults hide most of the dataset (open tasks only; active
workflows only) and neither endpoint has a value meaning "both". `all` is
therefore the CLI merging several calls, which is what these tests pin down.
"""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import respx
import typer.main

from wealthbox_tools.cli.main import app

_TASKS_URL = "https://api.crmworkspace.com/v1/tasks"
_WORKFLOWS_URL = "https://api.crmworkspace.com/v1/workflows"


def _list_command_params() -> list:
    """Return the Click params registered on `wbox tasks list`."""
    root = typer.main.get_command(app)
    return list(root.commands["tasks"].commands["list"].params)


def _params(call) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(str(call.request.url)).query).items()}


def _tasks(*ids: int) -> dict:
    return {
        "tasks": [{"id": i, "name": f"t{i}", "updated_at": "2026-01-02 10:00 AM -0700"} for i in ids],
        "meta": {"total_count": len(ids)},
    }


# --- tasks -----------------------------------------------------------------

@respx.mock
def test_tasks_default_status_requests_open_only(runner) -> None:
    respx.get(_TASKS_URL).mock(return_value=httpx.Response(200, json=_tasks(1)))
    result = runner.invoke(app, ["tasks", "list"])
    assert result.exit_code == 0
    assert len(respx.calls) == 1
    assert _params(respx.calls[0])["completed"] == "false"


@respx.mock
def test_tasks_status_completed_is_one_call(runner) -> None:
    respx.get(_TASKS_URL).mock(return_value=httpx.Response(200, json=_tasks(2)))
    result = runner.invoke(app, ["tasks", "list", "--status", "completed"])
    assert result.exit_code == 0
    assert len(respx.calls) == 1
    assert _params(respx.calls[0])["completed"] == "true"


@respx.mock
def test_tasks_status_all_makes_two_calls_and_merges(runner) -> None:
    respx.get(_TASKS_URL).mock(
        side_effect=[
            httpx.Response(200, json=_tasks(1, 2)),
            httpx.Response(200, json=_tasks(2, 3)),
        ]
    )
    result = runner.invoke(app, ["tasks", "list", "--status", "all"])
    assert result.exit_code == 0
    assert len(respx.calls) == 2
    assert [_params(c)["completed"] for c in respx.calls] == ["false", "true"]
    # id 2 appears in both batches but only once in the output.
    assert result.stdout.count('"id"') == 3


@respx.mock
def test_include_completed_is_a_hidden_alias_for_all(runner) -> None:
    """The old flag mapped to `completed=true` — completed *only*, the opposite
    of its name. It now means --status all, so old skill prompts stay correct."""
    respx.get(_TASKS_URL).mock(
        side_effect=[
            httpx.Response(200, json=_tasks(1)),
            httpx.Response(200, json=_tasks(2)),
        ]
    )
    result = runner.invoke(app, ["tasks", "list", "--include-completed"])
    assert result.exit_code == 0
    assert len(respx.calls) == 2
    assert [_params(c)["completed"] for c in respx.calls] == ["false", "true"]


def test_include_completed_is_hidden_but_status_is_not() -> None:
    """Assert against the Click command, not rendered help text.

    Scraping `--help` output couples the test to Rich's wrapping, which differs
    between a developer console and CI. The command tree is what actually
    decides whether a flag is advertised, and it is also what the skill-ref
    generator reads (it skips `param.hidden`), so checking it covers both.
    """
    params = {p.name: p for p in _list_command_params()}
    assert params["include_completed"].hidden is True
    assert params["status"].hidden is False


# --- workflows -------------------------------------------------------------

def _workflows(*ids: int) -> dict:
    return {
        "workflows": [{"id": i, "label": f"w{i}", "updated_at": "2026-01-02 10:00 AM -0700"} for i in ids],
        "meta": {"total_count": len(ids)},
    }


@respx.mock
def test_workflows_default_status_is_explicitly_active(runner) -> None:
    respx.get(_WORKFLOWS_URL).mock(return_value=httpx.Response(200, json=_workflows(1)))
    result = runner.invoke(app, ["workflows", "list"])
    assert result.exit_code == 0
    assert len(respx.calls) == 1
    assert _params(respx.calls[0])["status"] == "active"


@respx.mock
def test_workflows_status_all_makes_three_calls_and_merges(runner) -> None:
    respx.get(_WORKFLOWS_URL).mock(
        side_effect=[
            httpx.Response(200, json=_workflows(1)),
            httpx.Response(200, json=_workflows(1, 2)),
            httpx.Response(200, json=_workflows(3)),
        ]
    )
    result = runner.invoke(app, ["workflows", "list", "--status", "all"])
    assert result.exit_code == 0
    assert len(respx.calls) == 3
    assert [_params(c)["status"] for c in respx.calls] == ["active", "completed", "scheduled"]
    assert result.stdout.count('"id"') == 3


@respx.mock
def test_workflows_single_status_is_one_call(runner) -> None:
    respx.get(_WORKFLOWS_URL).mock(return_value=httpx.Response(200, json=_workflows(9)))
    result = runner.invoke(app, ["workflows", "list", "--status", "completed"])
    assert result.exit_code == 0
    assert len(respx.calls) == 1
    assert _params(respx.calls[0])["status"] == "completed"
