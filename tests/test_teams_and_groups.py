"""`wbox teams list` and `wbox users groups` — the lookups behind
`--assigned-to-team` and `visible_to`."""
from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app

_TEAMS = {
    "teams": [
        {
            "id": 194979,
            "name": "Associate Advisor Team",
            "members": [
                {"id": 1, "name": "Ada", "email": "ada@example.com"},
                {"id": 2, "name": "Grace", "email": "grace@example.com"},
            ],
        },
        {"id": 203280, "name": "Solo", "members": [{"id": 1, "name": "Ada"}]},
    ],
    "meta": {"total_count": 2, "total_pages": 1, "page": 1},
}

_GROUPS = {
    "user_groups": [
        {"id": 192799, "name": "Everyone", "user": None, "members": [1, 2, 3]},
        {"id": 192800, "name": "Only Me", "user": 1, "members": [1]},
    ],
    "meta": {"total_count": 2, "total_pages": 1, "page": 1},
}


@respx.mock
def test_teams_list_json_adds_member_count(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/teams").mock(
        return_value=httpx.Response(200, json=_TEAMS)
    )
    result = runner.invoke(app, ["teams", "list"])
    assert result.exit_code == 0
    assert '"member_count": 2' in result.stdout
    assert '"name": "Associate Advisor Team"' in result.stdout
    # Member objects are verbose-only.
    assert "ada@example.com" not in result.stdout


@respx.mock
def test_teams_list_table(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/teams").mock(
        return_value=httpx.Response(200, json=_TEAMS)
    )
    result = runner.invoke(app, ["teams", "list", "--format", "table"])
    assert result.exit_code == 0
    assert "member_count" in result.stdout
    assert "194979" in result.stdout


@respx.mock
def test_teams_list_verbose_keeps_members(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/teams").mock(
        return_value=httpx.Response(200, json=_TEAMS)
    )
    result = runner.invoke(app, ["teams", "list", "--verbose"])
    assert result.exit_code == 0
    assert "ada@example.com" in result.stdout


@respx.mock
def test_user_groups_list_json(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/user_groups").mock(
        return_value=httpx.Response(200, json=_GROUPS)
    )
    result = runner.invoke(app, ["users", "groups"])
    assert result.exit_code == 0
    assert '"member_count": 3' in result.stdout
    assert '"name": "Everyone"' in result.stdout


@respx.mock
def test_user_groups_list_table(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/user_groups").mock(
        return_value=httpx.Response(200, json=_GROUPS)
    )
    result = runner.invoke(app, ["users", "groups", "--format", "table"])
    assert result.exit_code == 0
    assert "192800" in result.stdout
    assert "Only Me" in result.stdout
