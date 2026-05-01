from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

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


def _install_and_bootstrap(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    _setup_api_mocks()
    runner.invoke(app, ["skills", "bootstrap"])


@respx.mock
def test_refresh_preserves_handedited_files(runner, tmp_path, monkeypatch):
    _install_and_bootstrap(runner, tmp_path, monkeypatch)
    firm = tmp_path / ".claude" / "skills" / "wealthbox-crm" / "firm"
    (firm / "contacts.md").write_text("MY POLICY\n")
    result = runner.invoke(app, ["skills", "refresh"])
    assert result.exit_code == 0, result.stdout
    assert (firm / "contacts.md").read_text() == "MY POLICY\n"


@respx.mock
def test_refresh_warns_when_meta_is_stale(runner, tmp_path, monkeypatch):
    _install_and_bootstrap(runner, tmp_path, monkeypatch)
    skill_root = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    meta_path = skill_root / "_meta.json"
    meta = json.loads(meta_path.read_text())
    stale = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    meta["firm"]["files"] = {k: stale for k in meta["firm"]["files"]}
    meta_path.write_text(json.dumps(meta) + "\n")
    result = runner.invoke(app, ["skills", "refresh", "--staleness-days", "30"])
    assert result.exit_code == 0, result.stdout
    output = (result.stdout or "") + (result.stderr or "")
    assert "stale" in output.lower()
