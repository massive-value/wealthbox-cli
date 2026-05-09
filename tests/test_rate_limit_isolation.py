"""Test isolation for the persistent rate-limit state file (issue #56).

The ``RateLimiter`` in ``wealthbox_tools.client.base`` persists timestamps
to ``~/.wbox_rate_limit.json`` so that throttling carries across CLI
invocations. Tests must NOT touch the developer's real file, otherwise a
full ``pytest`` run accumulates ~300 timestamps inside the rolling
5-minute window and later tests stall on real rate-limit logic.

These tests assert:

1. ``RateLimiter`` honours ``WBOX_RATE_LIMIT_STATE_FILE`` to override the
   default state path.
2. The autouse ``isolate_config_dir`` fixture sets that env var, so a
   freshly-constructed ``RateLimiter`` writes to the tmp dir, never to
   the user's real home file.
3. A poisoned file at ``~/.wbox_rate_limit.json`` does not affect tests:
   the limiter under test ignores it because the env var redirects it.
"""

from __future__ import annotations

import json
import os
import pathlib
import time

import pytest

from wealthbox_tools.client.base import RateLimiter, _WealthboxBase


def test_state_file_env_var_override(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """RateLimiter respects WBOX_RATE_LIMIT_STATE_FILE."""
    target = tmp_path / "custom_rate_limit.json"
    monkeypatch.setenv("WBOX_RATE_LIMIT_STATE_FILE", str(target))

    limiter = RateLimiter()
    assert limiter._state_file == target


def test_explicit_state_file_arg_wins_over_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """An explicit ``state_file=`` kwarg beats the env var."""
    env_target = tmp_path / "env.json"
    arg_target = tmp_path / "arg.json"
    monkeypatch.setenv("WBOX_RATE_LIMIT_STATE_FILE", str(env_target))

    limiter = RateLimiter(state_file=arg_target)
    assert limiter._state_file == arg_target


def test_autouse_fixture_redirects_state_file(tmp_path_factory: pytest.TempPathFactory) -> None:
    """The autouse ``isolate_config_dir`` fixture must point the limiter
    away from the user's real home directory.
    """
    state_path_str = os.environ.get("WBOX_RATE_LIMIT_STATE_FILE")
    assert state_path_str is not None, (
        "isolate_config_dir fixture should set WBOX_RATE_LIMIT_STATE_FILE"
    )

    state_path = pathlib.Path(state_path_str)
    real_home_file = pathlib.Path.home() / ".wbox_rate_limit.json"
    assert state_path != real_home_file, (
        "rate-limit state file should not be the user's real home file"
    )
    # On Windows, pytest's tmp_path lives under %USERPROFILE%, so "not
    # under home" would be too strict — just assert the file is NOT the
    # literal real-home path.
    limiter = RateLimiter()
    assert limiter._state_file == state_path


@pytest.mark.asyncio
async def test_poisoned_home_file_does_not_bleed_into_tests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Reproducer for #56.

    Simulate the dev-machine scenario where ``~/.wbox_rate_limit.json``
    is full of recent timestamps (a previous full pytest run filled it).
    With the autouse isolation in place, a brand-new client should NOT
    read those timestamps and should NOT stall on rate-limit logic.
    """
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    poisoned = fake_home / ".wbox_rate_limit.json"
    now_wall = time.time()
    # 350 recent timestamps = well over the 300/5-min limit. If the
    # limiter ever read this file, ``acquire()`` would block on
    # ``asyncio.sleep`` for the remainder of the window.
    poisoned.write_text(json.dumps({"timestamps": [now_wall - 1.0] * 350}))
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: fake_home))

    # ``isolate_config_dir`` (autouse) has already set
    # WBOX_RATE_LIMIT_STATE_FILE for this test, so ``RateLimiter()``
    # below should ignore the poisoned file entirely.
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr("wealthbox_tools.client.base.asyncio.sleep", fake_sleep)

    client = _WealthboxBase(token="test-token", rate_limit=True)
    try:
        # Sanity: the limiter's state file is NOT the poisoned file.
        assert client._rate_limiter is not None
        assert client._rate_limiter._state_file != poisoned
        # And no timestamps were carried over from the poisoned file.
        assert len(client._rate_limiter._timestamps) == 0

        # Acquire a slot — should be instant, no rate-limit sleeping.
        await client._rate_limiter.acquire()
    finally:
        await client.aclose()

    assert sleep_calls == [], (
        f"RateLimiter slept {sleep_calls} — poisoned ~/.wbox_rate_limit.json "
        "bled into the test. Issue #56 isolation is broken."
    )
