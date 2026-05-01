from __future__ import annotations

import json
from pathlib import Path

from wealthbox_tools.cli.main import app


def _install(runner, tmp_path, monkeypatch, platform: str = "claude-code-user") -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["skills", "install", "--platform", platform, "--no-bootstrap"]
    )
    assert result.exit_code == 0, result.stdout
    if platform == "codex":
        return tmp_path / ".codex" / "skills" / "wealthbox-crm"
    return tmp_path / ".claude" / "skills" / "wealthbox-crm"


def test_upgrade_refreshes_template_files(runner, tmp_path, monkeypatch):
    dest = _install(runner, tmp_path, monkeypatch)
    (dest / "SKILL.md").write_text("TAMPERED")

    result = runner.invoke(app, ["skills", "upgrade"])
    assert result.exit_code == 0, result.stdout
    assert (dest / "SKILL.md").read_text().startswith("---")  # frontmatter restored


def test_upgrade_preserves_firm_directory(runner, tmp_path, monkeypatch):
    dest = _install(runner, tmp_path, monkeypatch)
    firm = dest / "firm"
    firm.mkdir(exist_ok=True)
    (firm / "contacts.md").write_text("MY POLICY\n")
    (firm / "categories.md").write_text("# generated\n")

    result = runner.invoke(app, ["skills", "upgrade"])
    assert result.exit_code == 0, result.stdout
    assert (firm / "contacts.md").read_text() == "MY POLICY\n"
    assert (firm / "categories.md").read_text() == "# generated\n"


def test_upgrade_preserves_firm_meta_section(runner, tmp_path, monkeypatch):
    dest = _install(runner, tmp_path, monkeypatch)
    # Simulate bootstrap having written a firm section
    meta = json.loads((dest / "_meta.json").read_text())
    meta["firm"] = {
        "identity": {"id": 99, "name": "Test Firm"},
        "cli_version": "1.1.1",
        "files": {"categories.md": "2026-04-30T00:00:00+00:00"},
    }
    (dest / "_meta.json").write_text(json.dumps(meta) + "\n")

    result = runner.invoke(app, ["skills", "upgrade"])
    assert result.exit_code == 0, result.stdout
    after = json.loads((dest / "_meta.json").read_text())
    assert after["firm"]["identity"] == {"id": 99, "name": "Test Firm"}
    assert after["firm"]["cli_version"] == "1.1.1"


def test_upgrade_updates_template_cli_version(runner, tmp_path, monkeypatch):
    dest = _install(runner, tmp_path, monkeypatch)
    # Pretend an older version installed the template
    meta = json.loads((dest / "_meta.json").read_text())
    meta["template"]["cli_version"] = "1.0.0"
    (dest / "_meta.json").write_text(json.dumps(meta) + "\n")

    result = runner.invoke(app, ["skills", "upgrade"])
    assert result.exit_code == 0, result.stdout
    after = json.loads((dest / "_meta.json").read_text())
    assert after["template"]["cli_version"] != "1.0.0"
    # Output reports the version transition
    assert "1.0.0 ->" in result.stdout


def test_upgrade_errors_when_nothing_installed(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["skills", "upgrade"])
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "no installed" in output.lower()


def test_upgrade_codex_keeps_agents_md_and_no_skill_md(runner, tmp_path, monkeypatch):
    dest = _install(runner, tmp_path, monkeypatch, platform="codex")
    assert (dest / "AGENTS.md").exists()
    assert not (dest / "SKILL.md").exists()
    (dest / "AGENTS.md").write_text("TAMPERED")

    result = runner.invoke(app, ["skills", "upgrade"])
    assert result.exit_code == 0, result.stdout
    assert (dest / "AGENTS.md").read_text().startswith("---")
    assert not (dest / "SKILL.md").exists()


def test_upgrade_explicit_platform_flag(runner, tmp_path, monkeypatch):
    dest = _install(runner, tmp_path, monkeypatch)
    (dest / "SKILL.md").write_text("TAMPERED")

    result = runner.invoke(
        app, ["skills", "upgrade", "--platform", "claude-code-user"]
    )
    assert result.exit_code == 0, result.stdout
    assert (dest / "SKILL.md").read_text().startswith("---")


def test_upgrade_explicit_platform_must_be_installed(runner, tmp_path, monkeypatch):
    _install(runner, tmp_path, monkeypatch)  # claude-code-user only
    result = runner.invoke(
        app, ["skills", "upgrade", "--platform", "codex"]
    )
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "not installed" in output.lower()
