from __future__ import annotations

import os
import platform
from pathlib import Path

from wealthbox_tools.cli.main import app


def test_prefs_path_prints_canonical_path(tmp_path, monkeypatch, runner):
    """`wbox prefs path` prints the absolute preferences.md path on the current OS."""
    # Hermetic: redirect both XDG_CONFIG_HOME and APPDATA so the test never
    # touches the developer's real config dir.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    result = runner.invoke(app, ["prefs", "path"])
    assert result.exit_code == 0

    # _user_dir() resolves the path, which may canonicalise symlinks on
    # platforms where tmp_path lives under one (e.g. macOS /var → /private/var).
    expected = (tmp_path / "wbox" / "user").resolve() / "preferences.md"
    printed = result.stdout.strip()
    assert printed == str(expected)
    # Path must be absolute regardless of OS/cwd.
    assert os.path.isabs(printed)


def test_prefs_path_uses_appdata_on_windows(tmp_path, monkeypatch, runner):
    """On Windows the path must be rooted under %APPDATA%\\wbox\\user."""
    if platform.system() != "Windows":
        # The helper inspects platform.system() at call time, so this branch
        # only meaningfully exercises the Windows code path on Windows.
        return
    monkeypatch.setenv("APPDATA", str(tmp_path))

    result = runner.invoke(app, ["prefs", "path"])
    assert result.exit_code == 0
    expected = (tmp_path / "wbox" / "user").resolve() / "preferences.md"
    assert result.stdout.strip() == str(expected)


def test_prefs_show_prints_contents_when_file_exists(tmp_path, monkeypatch, runner):
    """`wbox prefs show` dumps preferences.md contents when present."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    user_dir = tmp_path / "wbox" / "user"
    user_dir.mkdir(parents=True)
    body = "# My prefs\n\n- favorite_color: blue\n"
    (user_dir / "preferences.md").write_text(body, encoding="utf-8")

    result = runner.invoke(app, ["prefs", "show"])
    assert result.exit_code == 0
    assert result.stdout == body


def test_prefs_show_empty_when_file_absent(tmp_path, monkeypatch, runner):
    """`wbox prefs show` exits 0 with empty stdout if the file is missing."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    # Create the user dir but no preferences.md inside it.
    (tmp_path / "wbox" / "user").mkdir(parents=True)

    result = runner.invoke(app, ["prefs", "show"])
    assert result.exit_code == 0
    assert result.stdout == ""


def test_prefs_show_empty_when_parent_dir_absent(tmp_path, monkeypatch, runner):
    """`wbox prefs show` exits 0 with empty stdout if the parent dir is missing."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    # No wbox/ at all.
    assert not (tmp_path / "wbox").exists()

    result = runner.invoke(app, ["prefs", "show"])
    assert result.exit_code == 0
    assert result.stdout == ""


def test_prefs_show_does_not_create_user_dir(tmp_path, monkeypatch, runner):
    """`wbox prefs show` must be read-only — no side effects on disk."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    result = runner.invoke(app, ["prefs", "show"])
    assert result.exit_code == 0
    # Confirm `show` did not lazily create the directory tree.
    assert not (tmp_path / "wbox" / "user").exists()


def test_prefs_path_does_not_create_user_dir(tmp_path, monkeypatch, runner):
    """`wbox prefs path` must not create the user directory."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))

    result = runner.invoke(app, ["prefs", "path"])
    assert result.exit_code == 0
    assert not (tmp_path / "wbox" / "user").exists()


def test_user_prefs_path_helper_matches_config_dir():
    """The helper used by `prefs` must mirror `_config_dir()` exactly.

    _user_dir() applies .resolve() to guarantee an absolute path even when
    XDG_CONFIG_HOME / APPDATA is set to a relative value, so we compare
    against the resolved equivalent here.
    """
    from wealthbox_tools.cli._config import _config_dir, _user_prefs_path

    expected = (_config_dir() / "user").resolve() / "preferences.md"
    assert _user_prefs_path() == expected
    assert isinstance(_user_prefs_path(), Path)


def test_prefs_path_is_absolute_when_xdg_relative(tmp_path, monkeypatch, runner):
    """`wbox prefs path` must print an absolute path even when the env var is relative.

    Codex P2 (PR #66): if XDG_CONFIG_HOME / APPDATA is set to a relative
    value, the underlying _config_dir() preserves that base, so the prefs
    helpers would otherwise return a path that depends on the caller's cwd.
    The new prefs slot's contract guarantees an absolute path; verify that
    by chdir'ing into a tmp dir and pointing the env var at a relative
    sibling directory.
    """
    # Run from inside tmp_path so a relative env var is interpretable but
    # the meaning depends on cwd (which is exactly what we want to defeat).
    monkeypatch.chdir(tmp_path)
    # "rel-config" is a relative path — without .resolve() in the helper,
    # _user_prefs_path() would return Path("rel-config/wbox/user/preferences.md").
    monkeypatch.setenv("XDG_CONFIG_HOME", "rel-config")
    monkeypatch.setenv("APPDATA", "rel-config")

    result = runner.invoke(app, ["prefs", "path"])
    assert result.exit_code == 0

    printed = result.stdout.strip()
    assert Path(printed).is_absolute(), f"expected absolute path, got: {printed!r}"
    # The resolved path must point inside our tmp_path (cwd) — confirms the
    # relative base was anchored to cwd at resolve time.
    assert printed.endswith(str(Path("rel-config") / "wbox" / "user" / "preferences.md"))
