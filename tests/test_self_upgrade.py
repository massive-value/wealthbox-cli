"""Tests for `wbox self upgrade` and the `self_upgrade` library module.

Covers the Module B tracer happy-path:
- `check()` compares the running version to the latest GitHub release.
- `apply()` downloads the platform binary, verifies SHA-256, and performs
  an atomic rename with a `.old.<ts>` breadcrumb.

The orchestrator must be platform-uniform: tests parameterize the install
root via `tmp_path` and the binary filename via the `_binary_name()` helper,
so the Windows test in #37 can slot in without touching this file.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import httpx
import pytest
import respx

import wealthbox_tools.self_upgrade as su
from wealthbox_tools import __version__
from wealthbox_tools.cli.main import app

_RELEASES_URL = "https://api.github.com/repos/massive-value/wealthbox-cli/releases/latest"


def _release_payload(tag: str, assets: list[dict]) -> dict:
    return {
        "tag_name": tag,
        "name": tag,
        "assets": assets,
    }


def _asset(name: str, url: str) -> dict:
    return {"name": name, "browser_download_url": url}


# ---------------------------------------------------------------------------
# check()
# ---------------------------------------------------------------------------


@respx.mock
def test_check_returns_none_when_up_to_date() -> None:
    """When latest GitHub release matches __version__, check() -> None."""
    tag = f"v{__version__}"
    payload = _release_payload(
        tag,
        [
            _asset("wbox-linux-x64", "https://example.com/wbox-linux-x64"),
            _asset("wbox-macos-x64", "https://example.com/wbox-macos-x64"),
            _asset("wbox-windows-x64.exe", "https://example.com/wbox-windows-x64.exe"),
            _asset("checksums.txt", "https://example.com/checksums.txt"),
        ],
    )
    respx.get(_RELEASES_URL).mock(return_value=httpx.Response(200, json=payload))

    result = su.check()

    assert result is None


@respx.mock
def test_check_returns_candidate_when_outdated(monkeypatch) -> None:
    """When latest > __version__, check() returns a populated NewVersion."""
    # Force the running version to something older than the release.
    monkeypatch.setattr(su, "_running_version", lambda: "0.0.1")

    body = b"new-binary-bytes"
    digest = hashlib.sha256(body).hexdigest()
    binary_url = "https://example.com/wbox-linux-x64"
    checksums_url = "https://example.com/checksums.txt"
    checksums_body = (
        f"{digest}  wbox-linux-x64\n"
        f"deadbeef  wbox-macos-x64\n"
        f"cafebabe  wbox-windows-x64.exe\n"
    ).encode()

    respx.get(_RELEASES_URL).mock(
        return_value=httpx.Response(
            200,
            json=_release_payload(
                "v9.9.9",
                [
                    _asset("wbox-linux-x64", binary_url),
                    _asset("wbox-macos-x64", "https://example.com/wbox-macos-x64"),
                    _asset("wbox-windows-x64.exe", "https://example.com/wbox-windows-x64.exe"),
                    _asset("checksums.txt", checksums_url),
                ],
            ),
        )
    )
    respx.get(checksums_url).mock(return_value=httpx.Response(200, content=checksums_body))

    # Force the platform asset selection to linux for deterministic testing.
    monkeypatch.setattr(su, "_asset_name_for_platform", lambda: "wbox-linux-x64")

    candidate = su.check()

    assert candidate is not None
    assert candidate.version == "9.9.9"
    assert candidate.binary_url == binary_url
    assert candidate.sha256.lower() == digest.lower()
    assert candidate.asset_name == "wbox-linux-x64"


# ---------------------------------------------------------------------------
# _perform_swap() — the pure rename unit shared by Unix apply() and the
# Windows deferred-swap helper. Parameterized over the binary filename so
# Unix-style ("wbox") and Windows-style ("wbox.exe") names share one test.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("binary_filename", ["wbox", "wbox.exe"])
def test_perform_swap_does_rename_pair(tmp_path: Path, binary_filename: str) -> None:
    """`_perform_swap` renames current → backup and partial → current.

    The swap *logic* is platform-uniform; only the *scheduling* of when this
    runs differs (in-process on Unix, in a child process after parent exit
    on Windows — see `_schedule_swap`).
    """
    current = tmp_path / binary_filename
    current.write_bytes(b"old-bytes")
    partial = tmp_path / f"{binary_filename}.partial.42"
    partial.write_bytes(b"new-bytes")
    backup = tmp_path / f"{binary_filename}.old.42"

    su._perform_swap(current, partial, backup)

    assert current.read_bytes() == b"new-bytes"
    assert backup.read_bytes() == b"old-bytes"
    assert not partial.exists()


# ---------------------------------------------------------------------------
# _build_powershell_command() — pure argv builder for the deferred-swap helper.
# ---------------------------------------------------------------------------


def test_build_powershell_command_returns_expected_argv_shape(tmp_path: Path) -> None:
    """argv list has the expected powershell flags and embeds runtime values.

    The returned list is passed to subprocess.Popen verbatim. The inline
    script must include the parent pid (for Get-Process polling), the
    timeout, the version (written to status file), and refer to the swap
    operation and the status filename.
    """
    argv = su._build_powershell_command(
        parent_pid=12345,
        current=tmp_path / "wbox.exe",
        partial=tmp_path / "wbox.exe.partial.42",
        backup=tmp_path / "wbox.exe.old.42",
        status_path=tmp_path / "wbox.upgrade.status",
        version="9.9.9",
        timeout_seconds=30,
    )

    # argv shape: powershell + flags + -Command + script.
    assert argv[0] == "powershell"
    assert "-NoProfile" in argv
    assert "-WindowStyle" in argv
    assert argv[argv.index("-WindowStyle") + 1] == "Hidden"
    assert "-Command" in argv

    script = argv[argv.index("-Command") + 1]

    # Embedded values used at runtime by the helper.
    assert "12345" in script  # parent pid for Get-Process polling
    assert "9.9.9" in script  # version string written into the status file
    assert "30" in script  # timeout seconds

    # Polling: helper waits for parent exit before renaming.
    assert "Get-Process" in script

    # Rename pair: helper does the swap after parent exit.
    assert "Move-Item" in script or "Rename-Item" in script

    # Status file is mentioned (helper writes it on success or failure).
    assert "wbox.upgrade.status" in script


def test_build_powershell_command_handles_paths_with_spaces(tmp_path: Path) -> None:
    """Paths with spaces must be safely quoted so the rename doesn't shell-explode."""
    spaced_dir = tmp_path / "Program Files" / "wbox"
    spaced_dir.mkdir(parents=True)

    argv = su._build_powershell_command(
        parent_pid=99,
        current=spaced_dir / "wbox.exe",
        partial=spaced_dir / "wbox.exe.partial.42",
        backup=spaced_dir / "wbox.exe.old.42",
        status_path=spaced_dir / "wbox.upgrade.status",
        version="9.9.9",
        timeout_seconds=30,
    )

    script = argv[argv.index("-Command") + 1]
    # The literal space-bearing path must appear inside single-quoted strings
    # so PowerShell treats it as one literal string, not as multiple tokens.
    assert "'" in script
    assert "Program Files" in script


# ---------------------------------------------------------------------------
# _schedule_deferred_swap() — Popen invocation with the right detachment flags.
# ---------------------------------------------------------------------------


def test_schedule_deferred_swap_invokes_popen_with_detached_flags(
    tmp_path: Path, monkeypatch
) -> None:
    """Popen invoked with the helper argv, detached flags, and DEVNULL stdio.

    The flags + DEVNULL combo is what lets the helper survive after the
    parent exits — without them the helper would inherit the parent's
    console and die with it, leaving the upgrade half-applied.
    """
    captured: dict = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

    monkeypatch.setattr(su.subprocess, "Popen", FakePopen)

    current = tmp_path / "wbox.exe"
    partial = tmp_path / "wbox.exe.partial.42"
    backup = tmp_path / "wbox.exe.old.42"

    su._schedule_deferred_swap(current, partial, backup, parent_pid=12345, version="9.9.9")

    # Popen received the PowerShell argv built by _build_powershell_command.
    args = captured["args"]
    assert args[0] == "powershell"
    assert "-Command" in args
    script = args[args.index("-Command") + 1]
    assert "12345" in script
    assert "9.9.9" in script

    # Helper must survive parent exit: detached + new process group + no
    # inherited stdio. The exact constants come from subprocess on Windows.
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    flags = captured["kwargs"].get("creationflags", 0)
    assert flags & DETACHED_PROCESS, f"DETACHED_PROCESS missing from creationflags={flags:#x}"
    assert flags & CREATE_NEW_PROCESS_GROUP, (
        f"CREATE_NEW_PROCESS_GROUP missing from creationflags={flags:#x}"
    )

    import subprocess as _subprocess

    assert captured["kwargs"].get("stdin") is _subprocess.DEVNULL
    assert captured["kwargs"].get("stdout") is _subprocess.DEVNULL
    assert captured["kwargs"].get("stderr") is _subprocess.DEVNULL


# ---------------------------------------------------------------------------
# apply()
# ---------------------------------------------------------------------------


@respx.mock
def test_apply_windows_defers_swap_to_helper(tmp_path: Path, monkeypatch) -> None:
    """On Windows-style fixtures, apply() must NOT rename the live binary in-process.

    Renaming a running .exe on Windows raises PermissionError (the OS holds an
    exclusive lock on the executable). Instead apply() schedules a deferred-swap
    helper, leaves the partial download on disk for the helper to swap in, and
    returns a result breadcrumb. The helper performs the rename after the parent
    process exits.
    """
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox.exe")
    monkeypatch.setattr(su, "_is_windows", lambda: True)

    install_root = tmp_path
    current = install_root / "wbox.exe"
    current.write_bytes(b"old-bytes")

    new_bytes = b"new-windows-bytes"
    digest = hashlib.sha256(new_bytes).hexdigest()
    binary_url = "https://example.com/wbox-windows-x64.exe"
    respx.get(binary_url).mock(return_value=httpx.Response(200, content=new_bytes))

    frozen_ts = 1_700_000_001
    monkeypatch.setattr(su.time, "time", lambda: frozen_ts)

    spawned: list[tuple[Path, Path, Path, int, str]] = []

    def fake_schedule(
        current_p: Path, partial_p: Path, backup_p: Path, parent_pid: int, version: str
    ) -> None:
        spawned.append((current_p, partial_p, backup_p, parent_pid, version))

    monkeypatch.setattr(su, "_schedule_deferred_swap", fake_schedule)

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox-windows-x64.exe",
    )

    result = su.apply(candidate, install_root=install_root)

    # Current binary must NOT have been replaced in-process — that's the whole point.
    assert current.read_bytes() == b"old-bytes"

    # Helper must have been scheduled exactly once with the expected paths.
    assert len(spawned) == 1
    spawned_current, spawned_partial, spawned_backup, spawned_pid, spawned_version = spawned[0]
    assert spawned_current == current
    assert spawned_partial == install_root / f"wbox.exe.partial.{frozen_ts}"
    assert spawned_backup == install_root / f"wbox.exe.old.{frozen_ts}"
    assert isinstance(spawned_pid, int) and spawned_pid > 0
    assert spawned_version == "9.9.9"

    # Partial must still be on disk for the helper to swap in.
    assert spawned_partial.exists()
    assert spawned_partial.read_bytes() == new_bytes

    # Result breadcrumb still points where the new binary will live.
    assert result.version == "9.9.9"
    assert result.installed_path == current
    assert result.backup_path == install_root / f"wbox.exe.old.{frozen_ts}"


@respx.mock
def test_apply_atomic_rename_unix(tmp_path: Path, monkeypatch) -> None:
    """apply() renames current binary to .old.<ts> and installs new bytes.

    Uses tmp_path as the install root so this is filesystem-isolated and
    platform-agnostic. The orchestrator must NOT branch on sys.platform.
    """
    # Pin the binary filename and platform policy to the Unix variant. On a
    # Windows CI runner this test still exercises the Unix code path; the
    # Windows-specific orchestration is covered by
    # `test_apply_windows_defers_swap_to_helper`.
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox")
    monkeypatch.setattr(su, "_is_windows", lambda: False)

    install_root = tmp_path
    current = install_root / "wbox"
    current.write_bytes(b"old-binary-bytes")

    new_bytes = b"new-binary-bytes-v9-9-9"
    digest = hashlib.sha256(new_bytes).hexdigest()
    binary_url = "https://example.com/wbox-linux-x64"

    respx.get(binary_url).mock(return_value=httpx.Response(200, content=new_bytes))

    # Freeze the timestamp so the .old.<ts> filename is deterministic.
    frozen_ts = 1_700_000_000
    monkeypatch.setattr(su.time, "time", lambda: frozen_ts)

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox-linux-x64",
    )

    result = su.apply(candidate, install_root=install_root)

    # New binary in place with new contents.
    assert current.exists()
    assert current.read_bytes() == new_bytes

    # Old binary preserved under the timestamped breadcrumb.
    backup = install_root / f"wbox.old.{frozen_ts}"
    assert backup.exists()
    assert backup.read_bytes() == b"old-binary-bytes"

    # And no leftover partial-download files in the install root.
    leftovers = list(install_root.glob("wbox.partial.*"))
    assert leftovers == [], f"unexpected partial leftovers: {leftovers}"

    # UpgradeResult exposes useful breadcrumbs for callers / future cleanup.
    assert result.version == "9.9.9"
    assert result.installed_path == current
    assert result.backup_path == backup


@respx.mock
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Execute bits are a POSIX concept; Windows has no equivalent.",
)
def test_apply_sets_executable_mode_unix(tmp_path: Path, monkeypatch) -> None:
    """apply() must leave the installed binary executable on Unix/macOS.

    Regression for Codex P1: `Path.open("wb")` in `_download` creates the
    partial with the process umask (usually 0644), so without an explicit
    chmod the upgraded `wbox` would silently lose its execute bit and
    fail to run after upgrade.
    """
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox")
    monkeypatch.setattr(su, "_is_windows", lambda: False)

    install_root = tmp_path
    current = install_root / "wbox"
    current.write_bytes(b"old-binary-bytes")

    new_bytes = b"new-binary-bytes-v9-9-9"
    digest = hashlib.sha256(new_bytes).hexdigest()
    binary_url = "https://example.com/wbox-linux-x64"

    respx.get(binary_url).mock(return_value=httpx.Response(200, content=new_bytes))

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox-linux-x64",
    )

    su.apply(candidate, install_root=install_root)

    # Any execute bit (owner/group/other) is sufficient to confirm the
    # fix; we set 0o755 unconditionally so all three should be present.
    assert current.stat().st_mode & 0o111


# ---------------------------------------------------------------------------
# _read_and_clear_upgrade_status() — next-launch reader for the status file
# the Windows helper writes after attempting the deferred swap.
# ---------------------------------------------------------------------------


def test_read_and_clear_upgrade_status_returns_parsed_dict_and_deletes_file(
    tmp_path: Path,
) -> None:
    """Reader parses the status JSON, unlinks the file, returns the dict."""
    install_root = tmp_path
    status_path = install_root / "wbox.upgrade.status"
    payload = {"result": "ok", "version": "9.9.9", "reason": None, "ts": 1700000000}
    status_path.write_text(json.dumps(payload))

    parsed = su._read_and_clear_upgrade_status(install_root)

    assert parsed == payload
    assert not status_path.exists()


def test_read_and_clear_upgrade_status_returns_none_when_no_file(tmp_path: Path) -> None:
    """No status file → reader returns None (no error, no side effect)."""
    assert su._read_and_clear_upgrade_status(tmp_path) is None


def test_read_and_clear_upgrade_status_handles_malformed_json(tmp_path: Path) -> None:
    """Malformed status file → reader returns None and removes the bad file.

    The reader must never raise — it's called on every wbox startup; a bad
    file would otherwise crash the CLI on every subsequent invocation.
    """
    install_root = tmp_path
    status_path = install_root / "wbox.upgrade.status"
    status_path.write_text("not-valid-json{{{")

    parsed = su._read_and_clear_upgrade_status(install_root)

    assert parsed is None
    assert not status_path.exists()


# ---------------------------------------------------------------------------
# CLI smoke
# ---------------------------------------------------------------------------


def test_self_upgrade_help_renders(runner) -> None:
    """`wbox self upgrade --help` must render without exceptions."""
    result = runner.invoke(app, ["self", "upgrade", "--help"])
    assert result.exit_code == 0
    assert "upgrade" in result.stdout.lower()


def test_main_callback_prints_pending_upgrade_status(runner, tmp_path, monkeypatch) -> None:
    """When a status file exists, the root callback prints its outcome to stderr.

    The status file is written by the Windows deferred-swap helper between CLI
    invocations; reading + clearing it on next launch is how the user learns
    the upgrade succeeded (or failed).
    """
    from wealthbox_tools.cli import self_cmd

    monkeypatch.setattr(self_cmd, "_default_install_root", lambda: tmp_path)

    status_path = tmp_path / "wbox.upgrade.status"
    status_path.write_text(
        json.dumps({"result": "ok", "version": "9.9.9", "reason": None, "ts": 1700000000})
    )

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "9.9.9" in result.stderr
    assert not status_path.exists()


def test_main_callback_prints_pending_upgrade_failure(runner, tmp_path, monkeypatch) -> None:
    """A failed upgrade status surfaces the reason and the recovery state."""
    from wealthbox_tools.cli import self_cmd

    monkeypatch.setattr(self_cmd, "_default_install_root", lambda: tmp_path)

    status_path = tmp_path / "wbox.upgrade.status"
    status_path.write_text(
        json.dumps(
            {
                "result": "failed",
                "version": "9.9.9",
                "reason": "timeout waiting for parent exit",
                "ts": 1700000000,
            }
        )
    )

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "9.9.9" in result.stderr
    assert "fail" in result.stderr.lower()
    assert "timeout waiting for parent exit" in result.stderr
    assert not status_path.exists()


def test_upgrade_cmd_windows_says_scheduled(runner, monkeypatch, tmp_path) -> None:
    """On Windows, `wbox self upgrade` reports the upgrade as 'Scheduled', not 'Installed'.

    The deferred-swap helper performs the actual rename after the parent
    exits, so claiming the upgrade is 'installed' before the parent exits
    would be misleading — and possibly false if the helper later fails.
    """
    monkeypatch.setattr(su, "_is_windows", lambda: True)
    monkeypatch.setattr(
        su,
        "check",
        lambda: su.NewVersion(
            version="9.9.9",
            binary_url="https://example.com/x",
            sha256="deadbeef",
            asset_name="wbox-windows-x64.exe",
        ),
    )
    fake_result = su.UpgradeResult(
        version="9.9.9",
        installed_path=tmp_path / "wbox.exe",
        backup_path=tmp_path / "wbox.exe.old.42",
    )
    monkeypatch.setattr(su, "apply", lambda candidate, install_root: fake_result)

    result = runner.invoke(app, ["self", "upgrade"])

    assert result.exit_code == 0, result.stdout
    assert "Scheduled" in result.stdout
    assert "9.9.9" in result.stdout
    # Must NOT claim the upgrade is installed yet — that's after parent exit.
    assert "Installed" not in result.stdout


def test_upgrade_cmd_unix_says_installed(runner, monkeypatch, tmp_path) -> None:
    """On Unix, the existing 'Installed v9.9.9' wording is preserved (regression)."""
    monkeypatch.setattr(su, "_is_windows", lambda: False)
    monkeypatch.setattr(
        su,
        "check",
        lambda: su.NewVersion(
            version="9.9.9",
            binary_url="https://example.com/x",
            sha256="deadbeef",
            asset_name="wbox-linux-x64",
        ),
    )
    fake_result = su.UpgradeResult(
        version="9.9.9",
        installed_path=tmp_path / "wbox",
        backup_path=tmp_path / "wbox.old.42",
    )
    monkeypatch.setattr(su, "apply", lambda candidate, install_root: fake_result)

    result = runner.invoke(app, ["self", "upgrade"])

    assert result.exit_code == 0, result.stdout
    assert "Installed" in result.stdout
    assert "9.9.9" in result.stdout
    assert "Scheduled" not in result.stdout


def test_main_callback_silent_when_no_status_file(runner, tmp_path, monkeypatch) -> None:
    """No status file → no startup-status output (the common case)."""
    from wealthbox_tools.cli import self_cmd

    monkeypatch.setattr(self_cmd, "_default_install_root", lambda: tmp_path)

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "upgrade" not in result.stderr.lower()


@respx.mock
def test_self_upgrade_cli_no_op_when_up_to_date(runner) -> None:
    """When already on latest, `wbox self upgrade` exits 0 without applying."""
    tag = f"v{__version__}"
    respx.get(_RELEASES_URL).mock(
        return_value=httpx.Response(
            200,
            json=_release_payload(
                tag,
                [
                    _asset("wbox-linux-x64", "https://example.com/wbox-linux-x64"),
                    _asset("checksums.txt", "https://example.com/checksums.txt"),
                ],
            ),
        )
    )

    result = runner.invoke(app, ["self", "upgrade"])
    assert result.exit_code == 0, result.stdout
