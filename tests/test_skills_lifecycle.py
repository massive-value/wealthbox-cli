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
            200, json={"id": 1, "name": "Adv", "account": "Firm"}
        )
    )


@respx.mock
def test_full_lifecycle(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _setup_api_mocks()

    # install
    r = runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    assert r.exit_code == 0, r.stdout
    dest = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    assert (dest / "SKILL.md").exists()

    # bootstrap
    r = runner.invoke(app, ["skills", "bootstrap"])
    assert r.exit_code == 0, r.stdout
    firm = dest / "firm"
    assert (firm / "_meta.json").exists()

    # mutate hand-edited file
    (firm / "contacts.md").write_text("# user policy\n")

    # refresh — hand-edited file survives, generated files re-written
    r = runner.invoke(app, ["skills", "refresh"])
    assert r.exit_code == 0, r.stdout
    assert (firm / "contacts.md").read_text() == "# user policy\n"
    assert (firm / "categories.md").exists()

    # doctor — green
    r = runner.invoke(app, ["skills", "doctor"])
    assert r.exit_code == 0, r.stdout
    assert "installed" in r.stdout.lower()
    assert "token ok" in r.stdout.lower()

    # uninstall
    r = runner.invoke(app, ["skills", "uninstall", "--yes"])
    assert r.exit_code == 0, r.stdout
    assert not dest.exists()

    # list shows not installed
    r = runner.invoke(app, ["skills", "list"])
    assert r.exit_code == 0
    assert "not installed" in r.stdout.lower()
