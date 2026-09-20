"""`wbox comments list` — resource filters, the time window, and the guard.

An unfiltered GET /comments scans the whole workspace (~8.5s per page of 100),
so the command refuses one rather than letting an agent discover it by waiting.
"""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from wealthbox_tools.cli.main import app

_URL = "https://api.crmworkspace.com/v1/comments"
_RESPONSE = {
    "comments": [
        {
            "id": 1,
            "creator": 7,
            "created_at": "2026-01-02 10:00 AM -0700",
            "updated_at": "2026-01-02 10:00 AM -0700",
            "body": {"text": "Called back", "html": "<p>Called back</p>"},
            "resource_type": "Task",
            "resource_id": 42,
        }
    ],
    "meta": {"total_count": 1},
}


def _params(call) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(str(call.request.url)).query).items()}


def test_unfiltered_list_is_refused_with_validation_exit_code(runner) -> None:
    result = runner.invoke(app, ["comments", "list"])
    assert result.exit_code == 1
    assert "8.5s per page" in result.stderr


@pytest.mark.parametrize(
    ("flag", "resource_type"),
    [
        ("--task", "Task"),
        ("--event", "Event"),
        ("--note", "StatusUpdates"),
        ("--opportunity", "Opportunity"),
        ("--project", "Project"),
        ("--workflow", "Workflow"),
    ],
)
@respx.mock
def test_each_resource_flag_maps_to_its_api_resource_type(runner, flag, resource_type) -> None:
    respx.get(_URL).mock(return_value=httpx.Response(200, json=_RESPONSE))
    result = runner.invoke(app, ["comments", "list", flag, "42"])
    assert result.exit_code == 0
    params = _params(respx.calls[0])
    assert params["resource_type"] == resource_type
    assert params["resource_id"] == "42"


@respx.mock
def test_window_alone_is_enough(runner) -> None:
    respx.get(_URL).mock(return_value=httpx.Response(200, json=_RESPONSE))
    result = runner.invoke(
        app, ["comments", "list", "--updated-since", "2026-01-01T00:00:00-07:00"]
    )
    assert result.exit_code == 0
    params = _params(respx.calls[0])
    assert params["updated_since"] == "2026-01-01T00:00:00-07:00"
    assert "resource_type" not in params


def test_two_resource_filters_are_rejected(runner) -> None:
    result = runner.invoke(app, ["comments", "list", "--task", "1", "--event", "2"])
    assert result.exit_code != 0
    assert "only one resource filter" in result.stderr.lower()


@respx.mock
def test_default_output_unnests_and_strips_the_body(runner) -> None:
    """Bodies arrive as {"text": <html>, "html": <html>} — both HTML. Left alone
    they bury the message in a table row."""
    respx.get(_URL).mock(return_value=httpx.Response(200, json=_RESPONSE))
    result = runner.invoke(app, ["comments", "list", "--task", "42"])
    assert result.exit_code == 0
    assert '"text": "Called back"' in result.stdout
    assert "<p>" not in result.stdout
    assert '"html"' not in result.stdout


@respx.mock
def test_table_output_is_one_readable_row(runner) -> None:
    respx.get(_URL).mock(return_value=httpx.Response(200, json=_RESPONSE))
    result = runner.invoke(app, ["comments", "list", "--task", "42", "--format", "table"])
    assert result.exit_code == 0
    assert "Called back" in result.stdout
    assert "<p>" not in result.stdout


@respx.mock
def test_table_output_truncates_a_long_body(runner) -> None:
    long_body = dict(_RESPONSE)
    long_body["comments"] = [{**_RESPONSE["comments"][0], "body": {"text": "x" * 500, "html": "x" * 500}}]
    respx.get(_URL).mock(return_value=httpx.Response(200, json=long_body))
    result = runner.invoke(app, ["comments", "list", "--task", "42", "--format", "table"])
    assert result.exit_code == 0
    assert "..." in result.stdout
    assert "x" * 200 not in result.stdout


@respx.mock
def test_verbose_keeps_the_full_record(runner) -> None:
    respx.get(_URL).mock(return_value=httpx.Response(200, json=_RESPONSE))
    result = runner.invoke(app, ["comments", "list", "--task", "42", "--verbose"])
    assert result.exit_code == 0
    assert '"html"' in result.stdout
    assert '"updated_at"' in result.stdout
