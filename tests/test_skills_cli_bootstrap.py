from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli._skill_paths import firm_dir, firm_meta_path
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


@respx.mock
def test_bootstrap_writes_all_firm_files(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _setup_api_mocks()

    result = runner.invoke(app, ["skills", "bootstrap"])
    assert result.exit_code == 0, result.stdout

    fd = firm_dir()
    for name in (
        "categories.md", "custom-fields.md", "users.md",
        "_README.md", "contacts.md", "tasks.md",
    ):
        assert (fd / name).exists(), f"missing {name}"
    # Firm meta lives at the canonical firm dir, not inside any skill install
    assert firm_meta_path().exists()


@respx.mock
def test_bootstrap_dry_run_writes_nothing(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _setup_api_mocks()

    result = runner.invoke(app, ["skills", "bootstrap", "--dry-run"])
    assert result.exit_code == 0, result.stdout
    fd = firm_dir()
    assert not fd.exists() or not any(fd.iterdir())


@respx.mock
def test_bootstrap_works_without_any_skill_installs(runner, tmp_path, monkeypatch):
    """Firm data is now machine-level, so bootstrap doesn't require any
    platform install to succeed."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _setup_api_mocks()

    result = runner.invoke(app, ["skills", "bootstrap"])

    assert result.exit_code == 0, result.stdout
    assert firm_meta_path().exists()
