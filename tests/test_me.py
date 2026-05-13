from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_BASE = "https://api.crmworkspace.com/v1"

_ME_RESPONSE = {
    "id": 70416,
    "name": "Kadin Bullock",
    "email": "kadin@example.com",
    "current_user": {
        "id": 152760,
        "name": "Kadin Bullock",
        "account": 31965,
    },
    "users": [
        {"id": 152760, "account": 31965},
    ],
}


@respx.mock
def test_me_user_id_prints_bare_integer(runner) -> None:
    """`wbox me user-id` must print current_user.id as a bare integer with a
    single trailing newline — no JSON wrapping — so it composes cleanly with
    command substitution: `--assigned-to "$(wbox me user-id)"`."""
    respx.get(f"{_BASE}/me").mock(return_value=httpx.Response(200, json=_ME_RESPONSE))

    result = runner.invoke(app, ["me", "user-id"])
    assert result.exit_code == 0, result.output
    assert result.output == "152760\n"


@respx.mock
def test_me_json_output_unchanged(runner) -> None:
    """Default `wbox me` (JSON) must be byte-identical to today's behaviour —
    the relabeling only affects --format table. No new keys, no renamed keys."""
    respx.get(f"{_BASE}/me").mock(return_value=httpx.Response(200, json=_ME_RESPONSE))

    result = runner.invoke(app, ["me"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data == _ME_RESPONSE
    assert "login_id" not in data
    assert "user_id (--assigned-to)" not in data


@respx.mock
def test_me_table_relabels_ids(runner) -> None:
    """`wbox me --format table` should rename top-level `id` to `login_id` and
    add a `user_id (--assigned-to)` row pulled from `current_user.id`, so the
    two IDs aren't confusable at a glance."""
    respx.get(f"{_BASE}/me").mock(return_value=httpx.Response(200, json=_ME_RESPONSE))

    result = runner.invoke(app, ["me", "--format", "table"])
    assert result.exit_code == 0, result.output
    assert "login_id" in result.output
    assert "70416" in result.output
    assert "user_id (--assigned-to)" in result.output
    assert "152760" in result.output
    # The bare `id` label should no longer appear on its own row.
    # tabulate renders `| login_id |`, so a standalone `| id |` would indicate
    # we failed to relabel.
    assert "| id " not in result.output


@respx.mock
def test_me_user_id_missing_current_user(runner) -> None:
    """If the API response somehow lacks `current_user.id`, fail loudly with a
    non-zero exit code rather than printing nothing or `None`."""
    respx.get(f"{_BASE}/me").mock(
        return_value=httpx.Response(200, json={"id": 70416, "name": "X"})
    )

    result = runner.invoke(app, ["me", "user-id"])
    assert result.exit_code != 0
