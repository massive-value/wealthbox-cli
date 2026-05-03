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
    # Firm/ no longer ships inside the skill install
    assert not (dest / "firm").exists()
    # Per-install meta has only the template section
    assert (dest / "_meta.json").exists()

    # bootstrap (writes to canonical firm path, not into the skill dir)
    r = runner.invoke(app, ["skills", "bootstrap"])
    assert r.exit_code == 0, r.stdout
    fd = firm_dir()
    assert firm_meta_path().exists()
    assert (fd / "categories.md").exists()
    assert (fd / "contacts.md").exists()  # stub

    # mutate hand-edited file at canonical
    (fd / "contacts.md").write_text("# user policy\n")

    # refresh — hand-edited file survives, generated files re-written
    r = runner.invoke(app, ["skills", "refresh"])
    assert r.exit_code == 0, r.stdout
    assert (fd / "contacts.md").read_text() == "# user policy\n"
    assert (fd / "categories.md").exists()

    # firm-path command
    r = runner.invoke(app, ["skills", "firm-path"])
    assert r.exit_code == 0
    assert str(fd) in r.stdout

    # doctor — green
    r = runner.invoke(app, ["skills", "doctor"])
    assert r.exit_code == 0, r.stdout
    assert "installed" in r.stdout.lower()
    assert "token ok" in r.stdout.lower()

    # uninstall (firm/ at canonical is preserved)
    r = runner.invoke(app, ["skills", "uninstall", "--yes"])
    assert r.exit_code == 0, r.stdout
    assert not dest.exists()
    assert (fd / "contacts.md").read_text() == "# user policy\n"

    # list shows not installed but firm path still tracked
    r = runner.invoke(app, ["skills", "list"])
    assert r.exit_code == 0
    assert "not installed" in r.stdout.lower()
    assert "firm-path" in r.stdout.lower()
