from __future__ import annotations

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEALTHBOX_TOKEN", "test-token-123")


@pytest.fixture(autouse=True)
def isolate_config_dir(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Redirect `_config_dir()` to a tmp dir so firm/ data and config.json
    don't touch the developer's real ~/.config/wbox or %APPDATA%\\wbox."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
