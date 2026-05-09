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
    don't touch the developer's real ~/.config/wbox or %APPDATA%\\wbox.

    Also redirects RateLimiter's persistent state file
    (``~/.wbox_rate_limit.json``) into the same tmp dir. Without this
    redirect a full pytest run accumulates timestamps in the real file;
    once the rolling 5-minute window fills, later tests stall on real
    rate-limit logic and flake (issue #56).
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv(
        "WBOX_RATE_LIMIT_STATE_FILE", str(tmp_path / ".wbox_rate_limit.json")
    )


@pytest.fixture(autouse=True)
def clear_brief_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """`wbox --brief` mutates os.environ at runtime; ensure each test starts
    with a clean WBOX_BRIEF state regardless of prior test ordering."""
    monkeypatch.delenv("WBOX_BRIEF", raising=False)
