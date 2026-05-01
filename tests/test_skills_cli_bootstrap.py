from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app
from wealthbox_tools.models.enums import CategoryType, DocumentType

_BASE = "https://api.crmworkspace.com/v1"


def _setup_api_mocks():
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
        ).mock(return_value=httpx.Response(200, json={"custom_fields": []}))
    respx.get(f"{_BASE}/users").mock(
        return_value=httpx.Response(200, json={"users": []})
    )
    respx.get(f"{_BASE}/me").mock(
        return_value=httpx.Response(
            200, json={"id": 1, "name": "Adv", "accounts": [{"id": 100, "name": "Firm"}]}
        )
    )


def _install(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )


@respx.mock
def test_bootstrap_writes_all_firm_files(runner, tmp_path, monkeypatch):
    _install(runner, tmp_path, monkeypatch)
    _setup_api_mocks()
    result = runner.invoke(app, ["skills", "bootstrap"])
    assert result.exit_code == 0, result.stdout
    skill_root = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    firm = skill_root / "firm"
    for name in (
        "categories.md", "custom-fields.md", "users.md",
        "_README.md", "contacts.md", "tasks.md",
    ):
        assert (firm / name).exists(), f"missing {name}"
    # _meta.json now lives at the skill root, not inside firm/
    assert (skill_root / "_meta.json").exists()
    assert not (firm / "_meta.json").exists()


@respx.mock
def test_bootstrap_dry_run_writes_nothing(runner, tmp_path, monkeypatch):
    _install(runner, tmp_path, monkeypatch)
    _setup_api_mocks()
    firm = tmp_path / ".claude" / "skills" / "wealthbox-crm" / "firm"
    result = runner.invoke(app, ["skills", "bootstrap", "--dry-run"])
    assert result.exit_code == 0, result.stdout
    assert not firm.exists() or not any(firm.iterdir())


@respx.mock
def test_bootstrap_reports_no_install(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _setup_api_mocks()
    result = runner.invoke(app, ["skills", "bootstrap"])
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "no installed" in output.lower()
