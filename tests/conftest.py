from __future__ import annotations

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEALTHBOX_TOKEN", "test-token-123")
