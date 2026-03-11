from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_LONG_BODY = "B" * 600
_LIST_RESPONSE = {
    "stream_events": [
        {"id": 1, "body": _LONG_BODY, "updated_at": "2025-01-01"},
        {"id": 2, "body": "Short body", "updated_at": "2025-01-02"},
    ],
    "meta": {"next_cursor": None},
}


@respx.mock
def test_list_activity_truncates_body_by_default(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/activity").mock(
        return_value=httpx.Response(200, json=_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["activity", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    events = data["stream_events"]
    assert len(events[0]["body"]) == 503  # 500 chars + "..."
    assert events[0]["body"].endswith("...")
    assert events[1]["body"] == "Short body"


@respx.mock
def test_list_activity_verbose_shows_full_body(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/activity").mock(
        return_value=httpx.Response(200, json=_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["activity", "list", "--verbose"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stream_events"][0]["body"] == _LONG_BODY


@respx.mock
def test_list_activity_verbose_short_flag(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/activity").mock(
        return_value=httpx.Response(200, json=_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["activity", "list", "-v"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stream_events"][0]["body"] == _LONG_BODY
