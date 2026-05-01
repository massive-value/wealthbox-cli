from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli._skill_bootstrap import bootstrap_skill_dir
from wealthbox_tools.models.enums import CategoryType, DocumentType

_BASE = "https://api.crmworkspace.com/v1"


def _mock_all_categories():
    """Set up respx mocks for every category type and every custom-field doc type."""
    for ct in CategoryType:
        if ct is CategoryType.CUSTOM_FIELDS:
            continue
        respx.get(f"{_BASE}/categories/{ct.value}").mock(
            return_value=httpx.Response(200, json={ct.value: []})
        )
    for dt in DocumentType:
        respx.get(
            f"{_BASE}/categories/custom_fields",
            params={"document_type": dt.value},
        ).mock(
            return_value=httpx.Response(200, json={"custom_fields": []})
        )


def _me_response(*, user_id: int, user_name: str, firm_id: int, firm_name: str) -> httpx.Response:
    """Build a /me response matching the real Wealthbox API shape."""
    return httpx.Response(
        200,
        json={
            "id": user_id,
            "name": user_name,
            "email": "u@example.com",
            "accounts": [{"id": firm_id, "name": firm_name}],
        },
    )


@respx.mock
def test_bootstrap_writes_generated_and_stubs_first_time(tmp_path):
    skill_dir = tmp_path / "wealthbox-crm"
    skill_dir.mkdir()
    _mock_all_categories()
    respx.get(f"{_BASE}/users").mock(return_value=httpx.Response(200, json={"users": []}))
    respx.get(f"{_BASE}/me").mock(
        return_value=_me_response(user_id=7, user_name="Adv", firm_id=100, firm_name="Firm")
    )

    result = bootstrap_skill_dir(skill_dir, token="t", generated_only=False)

    firm = skill_dir / "firm"
    assert (firm / "categories.md").exists()
    assert (firm / "custom-fields.md").exists()
    assert (firm / "users.md").exists()
    assert (skill_dir / "_meta.json").exists()
    assert not (firm / "_meta.json").exists()
    assert (firm / "_README.md").exists()
    for n in (
        "contacts.md", "tasks.md", "notes.md", "events.md",
        "opportunities.md", "projects.md", "workflows.md",
    ):
        assert (firm / n).exists()
    assert result.wrote_stubs == 7


@respx.mock
def test_bootstrap_generated_only_preserves_stubs(tmp_path):
    skill_dir = tmp_path / "wealthbox-crm"
    skill_dir.mkdir()
    firm = skill_dir / "firm"
    firm.mkdir()
    (firm / "contacts.md").write_text("MY EDITS\n")
    _mock_all_categories()
    respx.get(f"{_BASE}/users").mock(return_value=httpx.Response(200, json={"users": []}))
    respx.get(f"{_BASE}/me").mock(
        return_value=_me_response(user_id=1, user_name="x", firm_id=2, firm_name="y")
    )

    result = bootstrap_skill_dir(skill_dir, token="t", generated_only=True)

    assert (firm / "contacts.md").read_text() == "MY EDITS\n"
    assert result.wrote_stubs == 0
    assert (firm / "categories.md").exists()


@respx.mock
def test_bootstrap_paginates_categories_and_users(tmp_path):
    """Categories and users with >100 entries must paginate, not silently truncate."""
    skill_dir = tmp_path / "wealthbox-crm"
    skill_dir.mkdir()

    page1 = [{"id": i, "name": f"Tag{i}"} for i in range(1, 101)]   # 100 items
    page2 = [{"id": i, "name": f"Tag{i}"} for i in range(101, 151)]  # 50 items

    def _tags_route(request):
        page = request.url.params.get("page", "1")
        if page == "1":
            return httpx.Response(200, json={"tags": page1, "meta": {"total_count": 150}})
        return httpx.Response(200, json={"tags": page2, "meta": {"total_count": 150}})

    respx.get(f"{_BASE}/categories/tags").mock(side_effect=_tags_route)

    for ct in CategoryType:
        if ct is CategoryType.CUSTOM_FIELDS or ct.value == "tags":
            continue
        respx.get(f"{_BASE}/categories/{ct.value}").mock(
            return_value=httpx.Response(200, json={ct.value: [], "meta": {"total_count": 0}})
        )
    for dt in DocumentType:
        respx.get(
            f"{_BASE}/categories/custom_fields",
            params={"document_type": dt.value},
        ).mock(return_value=httpx.Response(200, json={"custom_fields": [], "meta": {"total_count": 0}}))

    user_page1 = [{"id": i, "name": f"User{i}", "email": f"u{i}@x.com"} for i in range(1, 101)]
    user_page2 = [{"id": i, "name": f"User{i}", "email": f"u{i}@x.com"} for i in range(101, 121)]

    def _users_route(request):
        page = request.url.params.get("page", "1")
        if page == "1":
            return httpx.Response(200, json={"users": user_page1, "meta": {"total_count": 120}})
        return httpx.Response(200, json={"users": user_page2, "meta": {"total_count": 120}})

    respx.get(f"{_BASE}/users").mock(side_effect=_users_route)
    respx.get(f"{_BASE}/me").mock(
        return_value=_me_response(user_id=1, user_name="x", firm_id=2, firm_name="y")
    )

    bootstrap_skill_dir(skill_dir, token="t", generated_only=False)

    categories_md = (skill_dir / "firm" / "categories.md").read_text()
    assert "Tag150" in categories_md, "page-2 tag missing — pagination not happening"
    assert "Tag1 " in categories_md or "| 1 | Tag1 |" in categories_md
    users_md = (skill_dir / "firm" / "users.md").read_text()
    assert "User120" in users_md, "page-2 user missing — pagination not happening"


@respx.mock
def test_bootstrap_does_not_set_onboarded_at(tmp_path):
    """`wbox skills bootstrap` populates the API-derived parts of `firm` only;
    `firm.onboarded_at` is reserved for the agent-driven qualitative step."""
    skill_dir = tmp_path / "wealthbox-crm"
    skill_dir.mkdir()
    _mock_all_categories()
    respx.get(f"{_BASE}/users").mock(return_value=httpx.Response(200, json={"users": []}))
    respx.get(f"{_BASE}/me").mock(
        return_value=_me_response(user_id=1, user_name="x", firm_id=2, firm_name="y")
    )

    bootstrap_skill_dir(skill_dir, token="t", generated_only=False)

    meta = json.loads((skill_dir / "_meta.json").read_text())
    assert "firm" in meta
    assert "onboarded_at" not in meta["firm"]


@respx.mock
def test_bootstrap_preserves_existing_onboarded_at(tmp_path):
    """A re-run of `wbox skills bootstrap` (e.g. refresh) must not clobber the
    onboarded_at marker the agent set after the qualitative Q&A."""
    skill_dir = tmp_path / "wealthbox-crm"
    skill_dir.mkdir()
    (skill_dir / "_meta.json").write_text(json.dumps({
        "firm": {
            "identity": {"id": 2, "name": "y", "user_id": 1, "user_name": "x"},
            "cli_version": "1.0.0",
            "files": {"categories.md": "2026-01-01T00:00:00+00:00"},
            "onboarded_at": "2026-04-15T12:00:00+00:00",
        }
    }))
    _mock_all_categories()
    respx.get(f"{_BASE}/users").mock(return_value=httpx.Response(200, json={"users": []}))
    respx.get(f"{_BASE}/me").mock(
        return_value=_me_response(user_id=1, user_name="x", firm_id=2, firm_name="y")
    )

    bootstrap_skill_dir(skill_dir, token="t", generated_only=False)

    meta = json.loads((skill_dir / "_meta.json").read_text())
    assert meta["firm"]["onboarded_at"] == "2026-04-15T12:00:00+00:00"


@respx.mock
def test_bootstrap_records_firm_identity_in_meta(tmp_path):
    skill_dir = tmp_path / "wealthbox-crm"
    skill_dir.mkdir()
    _mock_all_categories()
    respx.get(f"{_BASE}/users").mock(return_value=httpx.Response(200, json={"users": []}))
    respx.get(f"{_BASE}/me").mock(
        return_value=_me_response(
            user_id=42, user_name="Kadin", firm_id=31965, firm_name="Squire Wealth Advisors"
        )
    )

    bootstrap_skill_dir(skill_dir, token="t", generated_only=False)

    meta = json.loads((skill_dir / "_meta.json").read_text())
    identity = meta["firm"]["identity"]
    assert identity["id"] == 31965
    assert identity["name"] == "Squire Wealth Advisors"
    assert identity["user_id"] == 42
    assert identity["user_name"] == "Kadin"
    assert "cli_version" in meta["firm"]
    assert meta["firm"]["files"]  # at least one generated-file timestamp
