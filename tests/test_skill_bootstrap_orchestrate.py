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
    assert (firm / "_meta.json").exists()
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

    meta = json.loads((skill_dir / "firm" / "_meta.json").read_text())
    assert meta["firm"]["id"] == 31965
    assert meta["firm"]["name"] == "Squire Wealth Advisors"
    assert meta["firm"]["user_id"] == 42
    assert meta["firm"]["user_name"] == "Kadin"
