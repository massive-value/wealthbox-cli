"""Regression tests: skills bootstrap must honor every token source the rest of
the CLI honors (--token > WEALTHBOX_TOKEN > config file > .env).

Before v1.1.5, ``bootstrap_skill_dir`` constructed ``WealthboxClient`` directly
and only fell back to the env var, ignoring tokens stored via
``wbox config set-token``.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from wealthbox_tools.cli._config import save_config
from wealthbox_tools.cli.main import app
from wealthbox_tools.models.enums import CategoryType, DocumentType

_BASE = "https://api.crmworkspace.com/v1"


@pytest.fixture
def config_token_only(monkeypatch, tmp_path):
    """Isolate every token source EXCEPT the config file, then write a config-file token."""
    monkeypatch.delenv("WEALTHBOX_TOKEN", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
    monkeypatch.chdir(tmp_path)
    save_config({"token": "config-file-token"})


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
def test_bootstrap_uses_config_file_token_when_env_unset(runner, config_token_only):
    """`wbox skills bootstrap` must succeed when only a config-file token is set."""
    _setup_api_mocks()

    install = runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    assert install.exit_code == 0, install.stdout

    result = runner.invoke(app, ["skills", "bootstrap"])
    assert result.exit_code == 0, (result.stdout, result.stderr)
    assert "OK bootstrapped" in result.stdout


@respx.mock
def test_bootstrap_sends_config_file_token_in_header(runner, config_token_only):
    """The token reaches the API as the ACCESS_TOKEN header."""
    _setup_api_mocks()

    runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    runner.invoke(app, ["skills", "bootstrap"])

    me_calls = [c for c in respx.calls if c.request.url.path.endswith("/me")]
    assert me_calls, "bootstrap never called /me"
    assert me_calls[0].request.headers.get("ACCESS_TOKEN") == "config-file-token"


@respx.mock
def test_refresh_uses_config_file_token_when_env_unset(runner, config_token_only):
    """`wbox skills refresh` shares the bootstrap token-resolution path."""
    _setup_api_mocks()

    runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    runner.invoke(app, ["skills", "bootstrap"])

    result = runner.invoke(app, ["skills", "refresh"])
    assert result.exit_code == 0, (result.stdout, result.stderr)
