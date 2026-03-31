from __future__ import annotations

import json

from wealthbox_tools.cli.main import app


def test_config_set_token_and_show(tmp_path, monkeypatch, runner):
    """set-token stores a token, show displays it masked."""
    config_dir = tmp_path / "wbox"
    monkeypatch.setattr(
        "wealthbox_tools.cli._config._config_dir",
        lambda: config_dir,
    )

    # Set token
    result = runner.invoke(app, ["config", "set-token", "--token", "test-abc-12345"])
    assert result.exit_code == 0
    assert "Token saved" in result.output

    # Verify file
    config = json.loads((config_dir / "config.json").read_text())
    assert config["token"] == "test-abc-12345"

    # Show (masked)
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "...2345" in result.output


def test_config_clear(tmp_path, monkeypatch, runner):
    """clear removes the config file."""
    config_dir = tmp_path / "wbox"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(json.dumps({"token": "abc"}))

    monkeypatch.setattr(
        "wealthbox_tools.cli._config._config_dir",
        lambda: config_dir,
    )

    result = runner.invoke(app, ["config", "clear"])
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert not (config_dir / "config.json").exists()


def test_config_show_empty(tmp_path, monkeypatch, runner):
    """show with no config prints helpful message."""
    monkeypatch.setattr(
        "wealthbox_tools.cli._config._config_dir",
        lambda: tmp_path / "nonexistent",
    )

    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "No configuration found" in result.output


def test_config_clear_nonexistent(tmp_path, monkeypatch, runner):
    """clear with no config file is a no-op."""
    monkeypatch.setattr(
        "wealthbox_tools.cli._config._config_dir",
        lambda: tmp_path / "nonexistent",
    )

    result = runner.invoke(app, ["config", "clear"])
    assert result.exit_code == 0
    assert "No configuration to clear" in result.output
