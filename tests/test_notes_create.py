from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_NOTE_RESPONSE = {"id": 1, "content": "Test note", "linked_to": None}


@respx.mock
def test_add_note_content_only(runner) -> None:
    respx.post("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json=_NOTE_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "add", "Portfolio review call"])
    assert result.exit_code == 0


@respx.mock
def test_add_note_with_contact(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json=_NOTE_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "add", "Review call", "--contact", "123"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 123, "type": "Contact"}]


@respx.mock
def test_add_note_contact_and_project(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json=_NOTE_RESPONSE)
    )
    result = runner.invoke(
        app, ["notes", "add", "Review", "--contact", "123", "--project", "456"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [
        {"id": 123, "type": "Contact"},
        {"id": 456, "type": "Project"},
    ]


def test_add_note_missing_content(runner) -> None:
    result = runner.invoke(app, ["notes", "add"])
    assert result.exit_code != 0
