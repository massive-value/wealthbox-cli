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
            _asset("SHA256SUMS.txt", "https://example.com/SHA256SUMS.txt"),
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
    checksums_url = "https://example.com/SHA256SUMS.txt"
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
                    _asset("SHA256SUMS.txt", checksums_url),
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


def test_build_powershell_command_rolls_back_backup_on_swap_failure(tmp_path: Path) -> None:
    """If retries exhaust, the helper must move $backup → $current before failing.

    Codex P2 on PR #68: when current→backup succeeds but partial→current keeps
    failing, the user is left without a runnable wbox.exe and has no way to
    recover. The helper must restore the original binary before declaring
    failure so the user can at least run `wbox self upgrade` again.
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

    script = argv[argv.index("-Command") + 1]

    # Slice out the failure-handling block — everything after the retry loop's
    # exit when $swapped is false. Look for the move-backup-to-current pattern.
    rename_failed_idx = script.find("rename failed")
    assert rename_failed_idx != -1, "expected the rename-failed reason string in script"

    # The rollback should appear in the failure block: Move-Item with $backup
    # as the source (LiteralPath) and $current as the destination.
    pre_status_block = script[: rename_failed_idx]
    assert "Move-Item -LiteralPath $backup" in pre_status_block, (
        f"expected backup → current rollback before failure status; script:\n{script}"
    )


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
@pytest.mark.parametrize("binary_filename", ["wbox", "wbox.exe"])
def test_apply_atomic_rename(
    tmp_path: Path, monkeypatch, binary_filename: str
) -> None:
    """apply() renames current binary to .old.<ts> and installs new bytes.

    Parameterized over the binary filename so a single test exercises both
    the POSIX (`wbox`) and Windows (`wbox.exe`) layouts via the
    `_binary_name()` seam. `_is_windows()` is also pinned to False so the
    parameterized run on a Windows CI runner exercises the in-process
    Unix swap path here; the deferred-swap orchestration is covered by
    `test_apply_windows_defers_swap_to_helper`.
    """
    monkeypatch.setattr(su, "_binary_name", lambda: binary_filename)
    monkeypatch.setattr(su, "_is_windows", lambda: False)

    install_root = tmp_path
    current = install_root / binary_filename
    current.write_bytes(b"old-binary-bytes")

    new_bytes = b"new-binary-bytes-v9-9-9"
    digest = hashlib.sha256(new_bytes).hexdigest()
    binary_url = f"https://example.com/{binary_filename}"

    respx.get(binary_url).mock(return_value=httpx.Response(200, content=new_bytes))

    # Freeze the timestamp so the .old.<ts> filename is deterministic.
    frozen_ts = 1_700_000_000
    monkeypatch.setattr(su.time, "time", lambda: frozen_ts)

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name=binary_filename,
    )

    result = su.apply(candidate, install_root=install_root)

    # New binary in place with new contents.
    assert current.exists()
    assert current.read_bytes() == new_bytes

    # Old binary preserved under the timestamped breadcrumb.
    backup = install_root / f"{binary_filename}.old.{frozen_ts}"
    assert backup.exists()
    assert backup.read_bytes() == b"old-binary-bytes"

    # And no leftover partial-download files in the install root.
    leftovers = list(install_root.glob(f"{binary_filename}.partial.*"))
    assert leftovers == [], f"unexpected partial leftovers: {leftovers}"

    # UpgradeResult exposes useful breadcrumbs for callers / future cleanup.
    assert result.version == "9.9.9"
    assert result.installed_path == current
    assert result.backup_path == backup


@respx.mock
def test_apply_does_not_swap_when_checksum_mismatches(
    tmp_path: Path, monkeypatch
) -> None:
    """Regression for #38: a corrupted download must not touch the install.

    When the downloaded bytes do not match the manifest's SHA-256, ``apply()``
    must raise :class:`ChecksumMismatchError` BEFORE any rename happens.
    The pre-existing binary stays in place verbatim, no ``.old.<ts>``
    breadcrumb is created, and the partial download is cleaned up.
    """
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox")

    install_root = tmp_path
    current = install_root / "wbox"
    current.write_bytes(b"old-binary-bytes")

    # Server returns these bytes...
    served_bytes = b"corrupted-or-tampered-bytes"
    binary_url = "https://example.com/wbox-linux-x64"
    respx.get(binary_url).mock(return_value=httpx.Response(200, content=served_bytes))

    # ...but the manifest claims a different (deliberately wrong) digest.
    wrong_digest = "0" * 64
    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=wrong_digest,
        asset_name="wbox-linux-x64",
    )

    with pytest.raises(su.ChecksumMismatchError):
        su.apply(candidate, install_root=install_root)

    # Pre-existing binary is untouched, byte-for-byte.
    assert current.exists()
    assert current.read_bytes() == b"old-binary-bytes"

    # No backup breadcrumb was created — the rename never ran.
    assert list(install_root.glob("wbox.old.*")) == []

    # The except branch in apply() cleans up the partial download.
    assert list(install_root.glob("wbox.partial.*")) == []


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


@respx.mock
@pytest.mark.skipif(
    sys.platform != "win32",
    reason="Open-handle rename semantics are Windows-specific.",
)
def test_apply_rename_succeeds_with_open_handle_on_windows(
    tmp_path: Path, monkeypatch
) -> None:
    """apply() must complete the swap when a handle on the source path mirrors
    how Windows holds a running ``.exe``.

    Windows opens executable images with ``FILE_SHARE_READ |
    FILE_SHARE_DELETE``, which is what makes ``os.replace`` of a running
    binary feasible (the rename targets the directory entry, not the
    handle). Python's :func:`open` does NOT pass ``FILE_SHARE_DELETE``, so
    we acquire a handle via ``CreateFileW`` with the same share mode as
    the loader, then exercise :func:`apply` and assert the swap completes.

    Pin this contract with a regression test so a future refactor (e.g. a
    naive ``os.rename`` swap, or dropping ``FILE_SHARE_DELETE``) trips the
    test rather than shipping broken behavior.
    """
    import ctypes
    from ctypes import wintypes

    monkeypatch.setattr(su, "_binary_name", lambda: "wbox.exe")
    # Force the in-process Unix swap path so the test exercises the actual
    # `os.replace` against the held FILE_SHARE_DELETE handle. With the real
    # `_is_windows()` apply() would dispatch to `_schedule_deferred_swap`,
    # which polls for parent exit and is covered separately.
    monkeypatch.setattr(su, "_is_windows", lambda: False)

    install_root = tmp_path
    current = install_root / "wbox.exe"
    current.write_bytes(b"old-binary-bytes")

    new_bytes = b"new-binary-bytes-v9-9-9"
    digest = hashlib.sha256(new_bytes).hexdigest()
    binary_url = "https://example.com/wbox.exe"

    respx.get(binary_url).mock(return_value=httpx.Response(200, content=new_bytes))

    frozen_ts = 1_700_000_000
    monkeypatch.setattr(su.time, "time", lambda: frozen_ts)

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox.exe",
    )

    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.restype = wintypes.HANDLE
    CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    CloseHandle = ctypes.windll.kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype = wintypes.BOOL

    handle = CreateFileW(
        str(current),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    assert handle != INVALID_HANDLE_VALUE, (
        f"CreateFileW failed with error {ctypes.get_last_error()}"
    )
    try:
        result = su.apply(candidate, install_root=install_root)
    finally:
        CloseHandle(handle)

    # New binary in place with new contents.
    assert current.exists()
    assert current.read_bytes() == new_bytes

    # Old binary preserved under the timestamped breadcrumb.
    backup = install_root / f"wbox.exe.old.{frozen_ts}"
    assert backup.exists()
    assert backup.read_bytes() == b"old-binary-bytes"

    assert result.installed_path == current
    assert result.backup_path == backup


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
# _cleanup_stale_backups()
# ---------------------------------------------------------------------------


def test_cleanup_stale_backups_removes_old_keeps_recent(
    tmp_path: Path, monkeypatch
) -> None:
    """Older-than-24h `.old.<ts>` is unlinked; recent breadcrumb is kept.

    Defensively: a sibling file whose trailing component is non-numeric
    must not be touched — we only sweep parseable timestamps.
    """
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox")

    frozen_now = 1_700_000_000
    old_ts = frozen_now - (su._BACKUP_RETENTION_SECONDS + 60)  # >24h old
    recent_ts = frozen_now - 60  # well within 24h

    old_backup = tmp_path / f"wbox.old.{old_ts}"
    recent_backup = tmp_path / f"wbox.old.{recent_ts}"
    junk_backup = tmp_path / "wbox.old.notanumber"
    old_backup.write_bytes(b"old")
    recent_backup.write_bytes(b"recent")
    junk_backup.write_bytes(b"junk")

    removed = su._cleanup_stale_backups(tmp_path, now=frozen_now)

    assert not old_backup.exists()
    assert recent_backup.exists()
    assert junk_backup.exists(), "non-numeric suffix must not be deleted"
    assert old_backup in removed
    assert recent_backup not in removed
    assert junk_backup not in removed


@respx.mock
def test_apply_sweeps_stale_backups_on_success(tmp_path: Path, monkeypatch) -> None:
    """A successful `apply()` sweeps prior `.old.<ts>` files older than 24h.

    The freshly-created backup from this run (timestamp = frozen now) must
    survive — it's the rollback path for THIS upgrade.
    """
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox")
    # Force the in-process Unix swap path so apply() actually performs the
    # rename here; on a Windows runner the real `_is_windows()` would
    # dispatch to `_schedule_deferred_swap` (PowerShell helper) and the
    # cleanup-after-rename behavior we're asserting wouldn't be observable.
    monkeypatch.setattr(su, "_is_windows", lambda: False)

    install_root = tmp_path
    current = install_root / "wbox"
    current.write_bytes(b"old-binary-bytes")

    # Pre-seed a very old `.old.<ts>` from a previous upgrade.
    frozen_now = 1_700_000_000
    stale_ts = frozen_now - (su._BACKUP_RETENTION_SECONDS + 3600)
    stale_backup = install_root / f"wbox.old.{stale_ts}"
    stale_backup.write_bytes(b"ancient-backup")

    new_bytes = b"new-binary-bytes-v9-9-9"
    digest = hashlib.sha256(new_bytes).hexdigest()
    binary_url = "https://example.com/wbox-linux-x64"
    respx.get(binary_url).mock(return_value=httpx.Response(200, content=new_bytes))

    monkeypatch.setattr(su.time, "time", lambda: frozen_now)

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox-linux-x64",
    )

    su.apply(candidate, install_root=install_root)

    # Stale breadcrumb is gone…
    assert not stale_backup.exists(), "apply() should have swept the stale backup"
    # …but the freshly-created backup from THIS run survives.
    fresh_backup = install_root / f"wbox.old.{frozen_now}"
    assert fresh_backup.exists()
    assert fresh_backup.read_bytes() == b"old-binary-bytes"


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
                    _asset("SHA256SUMS.txt", "https://example.com/SHA256SUMS.txt"),
                ],
            ),
        )
    )

    result = runner.invoke(app, ["self", "upgrade"])
    assert result.exit_code == 0, result.stdout


# ---------------------------------------------------------------------------
# Skills-upgrade subprocess wiring (#40)
#
# After a successful binary swap, `wbox skills upgrade` must run so the skill
# template is refreshed in lockstep with the new binary. On Unix the swap is
# synchronous so the subprocess fires inside `apply()`. On Windows the swap is
# deferred to a child process that runs after the parent exits, so `apply()`
# writes a marker file and the actual subprocess fires from the next-launch
# callback once the deferred swap is confirmed successful.
# ---------------------------------------------------------------------------


@respx.mock
def test_apply_invokes_skills_upgrade_on_unix(tmp_path: Path, monkeypatch) -> None:
    """After the synchronous Unix swap, apply() must invoke `wbox skills upgrade`.

    The subprocess is invoked using the just-installed binary so the freshly
    written executable does the template refresh — keeping the binary and skill
    template in lockstep on disk.
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

    invocations: list[tuple[Path, ...]] = []

    def fake_invoke(binary_path: Path) -> int:
        invocations.append((binary_path,))
        return 0

    monkeypatch.setattr(su, "_invoke_skills_upgrade", fake_invoke)

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox-linux-x64",
    )

    su.apply(candidate, install_root=install_root)

    assert len(invocations) == 1, (
        f"expected exactly one skills-upgrade invocation, got {invocations}"
    )
    assert invocations[0][0] == current


@respx.mock
def test_apply_unix_does_not_rollback_when_skills_upgrade_fails(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Skills-upgrade subprocess failure must NOT undo the binary swap.

    The binary is already in place; the user can re-run `wbox skills upgrade`
    manually. Tearing down the swap on a skills-upgrade hiccup would be a
    cure-worse-than-the-disease for what is essentially a template refresh.
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

    monkeypatch.setattr(su, "_invoke_skills_upgrade", lambda binary_path: 1)

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox-linux-x64",
    )

    # Must not raise — non-zero exit is a warning, not a failure.
    result = su.apply(candidate, install_root=install_root)

    # Binary swap is intact: new bytes in place, old bytes preserved as backup.
    assert current.read_bytes() == new_bytes
    assert result.backup_path.exists()
    assert result.backup_path.read_bytes() == b"old-binary-bytes"


@respx.mock
def test_apply_windows_writes_skills_upgrade_pending_marker(
    tmp_path: Path, monkeypatch
) -> None:
    """On Windows, apply() defers the swap and writes a skills-upgrade marker.

    The actual `wbox skills upgrade` subprocess can't run from the parent —
    the swap hasn't happened yet. Instead the marker tells the next-launch
    callback to fire the subprocess once the deferred swap is confirmed.
    """
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox.exe")
    monkeypatch.setattr(su, "_is_windows", lambda: True)
    monkeypatch.setattr(su, "_schedule_deferred_swap", lambda *a, **kw: None)

    install_root = tmp_path
    current = install_root / "wbox.exe"
    current.write_bytes(b"old-bytes")

    new_bytes = b"new-windows-bytes"
    digest = hashlib.sha256(new_bytes).hexdigest()
    binary_url = "https://example.com/wbox-windows-x64.exe"
    respx.get(binary_url).mock(return_value=httpx.Response(200, content=new_bytes))

    candidate = su.NewVersion(
        version="9.9.9",
        binary_url=binary_url,
        sha256=digest,
        asset_name="wbox-windows-x64.exe",
    )

    su.apply(candidate, install_root=install_root)

    pending_marker = install_root / su._SKILLS_UPGRADE_PENDING_FILENAME
    assert pending_marker.exists(), (
        f"apply() should have written the skills-upgrade pending marker on Windows; "
        f"contents of install_root: {list(install_root.iterdir())}"
    )


def test_main_callback_runs_skills_upgrade_on_successful_deferred_swap(
    runner, tmp_path, monkeypatch
) -> None:
    """When the deferred swap succeeds AND a skills-upgrade marker is present,
    the next-launch callback fires `wbox skills upgrade` and clears the marker.
    """
    from wealthbox_tools.cli import self_cmd

    monkeypatch.setattr(self_cmd, "_default_install_root", lambda: tmp_path)
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox.exe")

    status_path = tmp_path / "wbox.upgrade.status"
    status_path.write_text(
        json.dumps({"result": "ok", "version": "9.9.9", "reason": None, "ts": 1700000000})
    )
    pending_marker = tmp_path / su._SKILLS_UPGRADE_PENDING_FILENAME
    pending_marker.write_text("")

    invocations: list[Path] = []

    def fake_invoke(binary_path: Path) -> int:
        invocations.append(binary_path)
        return 0

    monkeypatch.setattr(su, "_invoke_skills_upgrade", fake_invoke)

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0, result.stdout
    assert len(invocations) == 1
    assert invocations[0] == tmp_path / "wbox.exe"
    assert not pending_marker.exists(), (
        "the skills-upgrade pending marker must be cleared after running"
    )


def test_main_callback_skips_skills_upgrade_when_swap_failed(
    runner, tmp_path, monkeypatch
) -> None:
    """If the deferred swap failed, skills upgrade is NOT run.

    The marker is still cleared so it doesn't leak across runs — a future
    successful `wbox self upgrade` will write a fresh marker.
    """
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
    pending_marker = tmp_path / su._SKILLS_UPGRADE_PENDING_FILENAME
    pending_marker.write_text("")

    invocations: list[Path] = []

    def fake_invoke(binary_path: Path) -> int:
        invocations.append(binary_path)
        return 0

    monkeypatch.setattr(su, "_invoke_skills_upgrade", fake_invoke)

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0, result.stdout
    assert invocations == [], "skills upgrade must not run when the deferred swap failed"
    assert not pending_marker.exists(), (
        "marker must be cleared even when skill upgrade is skipped"
    )


def test_invoke_skills_upgrade_calls_subprocess_with_binary_path(
    tmp_path: Path, monkeypatch
) -> None:
    """`_invoke_skills_upgrade` runs `<binary> skills upgrade` and streams output.

    Output is streamed (not captured) so the user sees live progress; exit code
    is returned to the caller for warning-vs-rollback decisions.
    """
    binary_path = tmp_path / "wbox"
    binary_path.write_bytes(b"")

    captured: dict = {}

    class FakeCompleted:
        returncode = 0

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeCompleted()

    monkeypatch.setattr(su.subprocess, "run", fake_run)

    rc = su._invoke_skills_upgrade(binary_path)

    assert rc == 0
    assert captured["args"][0] == str(binary_path)
    assert captured["args"][1:] == ["skills", "upgrade"]
