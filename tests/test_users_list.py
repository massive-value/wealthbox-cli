from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_BASE = "https://api.crmworkspace.com/v1"


@respx.mock
def test_list_users_paginates_across_pages(runner) -> None:
    """`wbox users list` must walk every page; otherwise firms with >25
    users silently see a truncated list (the CLI exposes no --page flag)."""
    page1 = [{"id": i, "name": f"User{i}", "email": f"u{i}@x.com"} for i in range(1, 101)]
    page2 = [{"id": i, "name": f"User{i}", "email": f"u{i}@x.com"} for i in range(101, 121)]

    def _users_route(request: httpx.Request) -> httpx.Response:
        page = request.url.params.get("page", "1")
        if page == "1":
            return httpx.Response(200, json={"users": page1, "meta": {"total_count": 120}})
        return httpx.Response(200, json={"users": page2, "meta": {"total_count": 120}})

    respx.get(f"{_BASE}/users").mock(side_effect=_users_route)

    result = runner.invoke(app, ["users", "list", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data["users"]) == 120
    assert data["users"][0]["id"] == 1
    assert data["users"][-1]["id"] == 120
