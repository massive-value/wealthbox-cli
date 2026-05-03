from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

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


def _bootstrap(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _setup_api_mocks()
    runner.invoke(app, ["skills", "bootstrap"])


@respx.mock
def test_refresh_preserves_handedited_files(runner, tmp_path, monkeypatch):
    _bootstrap(runner, tmp_path, monkeypatch)
    fd = firm_dir()
    (fd / "contacts.md").write_text("MY POLICY\n")
    result = runner.invoke(app, ["skills", "refresh"])
    assert result.exit_code == 0, result.stdout
    assert (fd / "contacts.md").read_text() == "MY POLICY\n"


@respx.mock
def test_refresh_warns_when_meta_is_stale(runner, tmp_path, monkeypatch):
    _bootstrap(runner, tmp_path, monkeypatch)
    meta = json.loads(firm_meta_path().read_text())
    stale = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    meta["files"] = {k: stale for k in meta["files"]}
    firm_meta_path().write_text(json.dumps(meta) + "\n")
    result = runner.invoke(app, ["skills", "refresh", "--staleness-days", "30"])
    assert result.exit_code == 0, result.stdout
    output = (result.stdout or "") + (result.stderr or "")
    assert "stale" in output.lower()


@respx.mock
def test_refresh_errors_when_no_firm_meta(runner, tmp_path, monkeypatch):
    """Refresh requires bootstrap to have run first."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _setup_api_mocks()

    result = runner.invoke(app, ["skills", "refresh"])
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "bootstrap" in output.lower()
