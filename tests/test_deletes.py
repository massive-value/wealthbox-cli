"""Tests for delete commands across all resources that support deletion.

Resources with delete: contacts, tasks, events, opportunities.
Resources without delete (confirmed): notes (API does not support it),
projects, workflows (no CLI or client implementation).
"""
from __future__ import annotations

import httpx
import pytest
import respx

from wealthbox_tools.cli.main import app

BASE = "https://api.crmworkspace.com/v1"

# ---------------------------------------------------------------------------
# Parametrised fixtures: (cli_args_prefix, api_path_segment)
# ---------------------------------------------------------------------------
_RESOURCES = [
    pytest.param(["contacts", "delete"], "contacts", id="contacts"),
    pytest.param(["tasks", "delete"], "tasks", id="tasks"),
    pytest.param(["events", "delete"], "events", id="events"),
    pytest.param(["opportunities", "delete"], "opportunities", id="opportunities"),
]


# ---------------------------------------------------------------------------
# Success: 204 response
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cli_prefix,segment", _RESOURCES)
@respx.mock
def test_delete_success_204(runner, cli_prefix, segment) -> None:
    route = respx.delete(f"{BASE}/{segment}/42").mock(
        return_value=httpx.Response(204)
    )
    result = runner.invoke(app, cli_prefix + ["42"])
    assert result.exit_code == 0
    assert route.called
    assert route.call_count == 1
    assert "42" in result.output


@pytest.mark.parametrize("cli_prefix,segment", _RESOURCES)
@respx.mock
def test_delete_success_200(runner, cli_prefix, segment) -> None:
    """Some Wealthbox endpoints return 200 on delete; accept that too."""
    route = respx.delete(f"{BASE}/{segment}/7").mock(
        return_value=httpx.Response(200)
    )
    result = runner.invoke(app, cli_prefix + ["7"])
    assert result.exit_code == 0
    assert route.called
    assert "7" in result.output


# ---------------------------------------------------------------------------
# 404 → error: CLI exits 1, no success message emitted on stdout
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cli_prefix,segment", _RESOURCES)
@respx.mock
def test_delete_404_exits_nonzero(runner, cli_prefix, segment) -> None:
    respx.delete(f"{BASE}/{segment}/99").mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    result = runner.invoke(app, cli_prefix + ["99"])
    assert result.exit_code != 0
    # Error message goes to stderr, which CliRunner mixes into output by default.
    assert "404" in result.output


# ---------------------------------------------------------------------------
# Invalid ID: non-integer string is rejected by Typer before any HTTP call
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cli_prefix,segment", _RESOURCES)
@respx.mock
def test_delete_invalid_id_string(runner, cli_prefix, segment) -> None:
    """Passing a non-integer ID is rejected by Typer's type coercion;
    exit code is non-zero and no HTTP request is made."""
    result = runner.invoke(app, cli_prefix + ["abc"])
    assert result.exit_code != 0
    # No network call should have been made.
    assert respx.calls.call_count == 0
