from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_LONG_CONTENT = "A" * 600
_LIST_RESPONSE = {
    "status_updates": [
        {"id": 1, "content": _LONG_CONTENT, "linked_to": None, "creator_id": 5, "updated_at": "2025-01-01"},
        {"id": 2, "content": "Short note", "linked_to": None, "creator_id": 5, "updated_at": "2025-01-02"},
    ],
    "meta": {"current_page": 1, "total_pages": 1, "total_entries": 2},
}


@respx.mock
def test_list_notes_truncates_content_by_default(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json=_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    notes = data["status_updates"]
    # Long content should be truncated to 500 chars + ellipsis
    assert len(notes[0]["content"]) == 503  # 500 chars + "..."
    assert notes[0]["content"].endswith("...")
    # Short content should be unchanged
    assert notes[1]["content"] == "Short note"


@respx.mock
def test_list_notes_verbose_shows_full_content(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json=_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "list", "--verbose"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    notes = data["status_updates"]
    assert notes[0]["content"] == _LONG_CONTENT


@respx.mock
def test_list_notes_verbose_short_flag(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json=_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "list", "-v"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status_updates"][0]["content"] == _LONG_CONTENT


@respx.mock
def test_list_notes_default_fields_exclude_extras(runner) -> None:
    """Default (non-verbose) output should only include _DEFAULT_FIELDS."""
    full_note = {
        "id": 1,
        "content": "Short",
        "linked_to": None,
        "creator_id": 5,
        "updated_at": "2025-01-01",
        "extra_field": "should_be_hidden",
    }
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json={"status_updates": [full_note], "meta": {"current_page": 1}})
    )
    result = runner.invoke(app, ["notes", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "extra_field" not in data["status_updates"][0]
