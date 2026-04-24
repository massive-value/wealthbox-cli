from __future__ import annotations

from wealthbox_tools.cli.main import app


def test_set_token_help_mentions_token_page(runner):
    result = runner.invoke(app, ["config", "set-token", "--help"])
    assert result.exit_code == 0
    assert "dev.wealthbox.com" in result.stdout


def test_set_token_prints_hint(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    result = runner.invoke(app, ["config", "set-token"], input="abcd1234\n")
    assert result.exit_code == 0
    assert "dev.wealthbox.com" in result.stdout
