from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_HTML_HEAVY_NOTE = {
    "id": 1,
    "content": "Plain text",
    "content_html": "<div>Plain text</div>",
    "linked_to": [
        {
            "id": 99,
            "name": "Acme Corp",
            "description": "Plain",
            "description_html": "<p>Plain</p>",
        }
    ],
}


@respx.mock
def test_brief_env_var_strips_html_keys(runner, monkeypatch) -> None:
    """`WBOX_BRIEF=1` makes JSON output omit any `*_html` field, recursively.

    Wealthbox returns a markup-ified duplicate (description_html, content_html,
    body_html, etc.) of every text field, often 3-5x larger than the plain
    version and useless to an agent. Stripping these is the single biggest
    token-saving lever for the CLI.
    """
    monkeypatch.setenv("WBOX_BRIEF", "1")
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(
            200, json={"notes": [_HTML_HEAVY_NOTE], "meta": {"total_count": 1}}
        )
    )
    result = runner.invoke(app, ["notes", "list", "--verbose"])
    assert result.exit_code == 0
    out = json.loads(result.stdout)
    note = out["notes"][0]
    assert "content_html" not in note, "top-level *_html should be stripped"
    nested = note["linked_to"][0]
    assert "description_html" not in nested, "nested *_html should be stripped"
    # Plain text counterparts must remain.
    assert note["content"] == "Plain text"
    assert nested["description"] == "Plain"


@respx.mock
def test_brief_off_by_default(runner) -> None:
    """Without WBOX_BRIEF, html fields pass through unchanged."""
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(
            200, json={"notes": [_HTML_HEAVY_NOTE], "meta": {"total_count": 1}}
        )
    )
    result = runner.invoke(app, ["notes", "list", "--verbose"])
    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert "content_html" in out["notes"][0]


@respx.mock
def test_brief_root_flag_strips_html_keys(runner) -> None:
    """The root `wbox --brief ...` flag plumbs to the same behavior as the env var."""
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(
            200, json={"notes": [_HTML_HEAVY_NOTE], "meta": {"total_count": 1}}
        )
    )
    result = runner.invoke(app, ["--brief", "notes", "list", "--verbose"])
    assert result.exit_code == 0
    out = json.loads(result.stdout)
    assert "content_html" not in out["notes"][0]
