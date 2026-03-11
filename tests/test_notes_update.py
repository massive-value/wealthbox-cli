from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_NOTE_RESPONSE = {"id": 7, "content": "Updated content", "linked_to": None}


@respx.mock
def test_update_note_content(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/notes/7").mock(
        return_value=httpx.Response(200, json=_NOTE_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "update", "7", "--content", "Updated content"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["content"] == "Updated content"
    assert "linked_to" not in sent


@respx.mock
def test_update_note_with_contact(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/notes/7").mock(
        return_value=httpx.Response(200, json=_NOTE_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "update", "7", "--contact", "123"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 123, "type": "Contact"}]
    assert "content" not in sent


@respx.mock
def test_update_note_content_and_contact(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/notes/7").mock(
        return_value=httpx.Response(200, json=_NOTE_RESPONSE)
    )
    result = runner.invoke(
        app, ["notes", "update", "7", "--content", "New text", "--contact", "456"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["content"] == "New text"
    assert sent["linked_to"] == [{"id": 456, "type": "Contact"}]


def test_update_note_no_fields_raises(runner) -> None:
    result = runner.invoke(app, ["notes", "update", "7"])
    assert result.exit_code != 0
