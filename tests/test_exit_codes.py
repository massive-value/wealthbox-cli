"""Differentiated CLI exit codes + WBOX_DEBUG traceback path.

Exit-code scheme implemented in ``cli/_client.handle_errors``:

* 0 — success
* 1 — validation / user error (pydantic ValidationError, 4xx that isn't auth)
* 2 — auth error (WealthboxAPIError 401/403)
* 3 — server error (WealthboxAPIError >= 500)

Click/Typer usage errors (bad/missing args) also exit 2, but those are raised
by the parser before ``handle_errors`` runs and are out of scope here.
"""
from __future__ import annotations

import httpx
import pytest
import respx

from wealthbox_tools.cli.main import app

_BASE = "https://api.crmworkspace.com/v1"
_CONTACT_URL = f"{_BASE}/contacts/999999"


# --------------------------------------------------------------------------- #
# Auth errors -> exit 2
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("status", [401, 403])
@respx.mock
def test_auth_error_exits_2(runner, status: int) -> None:
    respx.get(_CONTACT_URL).mock(
        return_value=httpx.Response(status, json={"error": "Not authorized"})
    )
    result = runner.invoke(app, ["contacts", "get", "999999"])
    assert result.exit_code == 2, result.output
    assert f"API Error ({status})" in result.output


# --------------------------------------------------------------------------- #
# Server errors -> exit 3
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("status", [500, 503])
@respx.mock
def test_server_error_exits_3(runner, status: int) -> None:
    respx.get(_CONTACT_URL).mock(
        return_value=httpx.Response(status, json={"error": "Server blew up"})
    )
    result = runner.invoke(app, ["contacts", "get", "999999"])
    assert result.exit_code == 3, result.output
    assert f"API Error ({status})" in result.output


# --------------------------------------------------------------------------- #
# Non-auth 4xx -> exit 1
# --------------------------------------------------------------------------- #
@respx.mock
def test_not_found_404_exits_1(runner) -> None:
    respx.get(_CONTACT_URL).mock(
        return_value=httpx.Response(404, json={"error": "Not found"})
    )
    result = runner.invoke(app, ["contacts", "get", "999999"])
    assert result.exit_code == 1, result.output
    assert "API Error (404)" in result.output


@respx.mock
def test_validation_error_exits_1(runner) -> None:
    """A pydantic ValidationError exits 1.

    ``--birth-date not-a-date`` is a free-form CLI string (str | None at the
    Click layer) that is rejected by the contact-create input model's DateField
    validator, raising ValidationError inside handle_errors rather than at the
    Click parser layer.
    """
    result = runner.invoke(
        app,
        ["contacts", "add", "person", "--first-name", "X", "--birth-date", "not-a-date"],
    )
    assert result.exit_code == 1, result.output
    assert "Validation Error" in result.output
    # No HTTP request should have been made — validation fails first.
    assert respx.calls.call_count == 0


# --------------------------------------------------------------------------- #
# WBOX_DEBUG -> full traceback in addition to friendly message
# --------------------------------------------------------------------------- #
@respx.mock
def test_wbox_debug_emits_traceback(
    runner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("WBOX_DEBUG", "1")
    respx.get(_CONTACT_URL).mock(
        return_value=httpx.Response(500, json={"error": "Server blew up"})
    )
    result = runner.invoke(app, ["contacts", "get", "999999"])
    # Exit code stays meaningful even with the traceback printed.
    assert result.exit_code == 3, result.output
    assert "API Error (500)" in result.output
    assert "Traceback (most recent call last)" in result.output
    assert "WealthboxAPIError" in result.output


@respx.mock
def test_without_wbox_debug_no_traceback(runner) -> None:
    respx.get(_CONTACT_URL).mock(
        return_value=httpx.Response(500, json={"error": "Server blew up"})
    )
    result = runner.invoke(app, ["contacts", "get", "999999"])
    assert result.exit_code == 3, result.output
    assert "Traceback (most recent call last)" not in result.output
