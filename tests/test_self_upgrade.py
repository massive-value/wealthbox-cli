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
# apply()
# ---------------------------------------------------------------------------


@respx.mock
def test_apply_atomic_rename_unix(tmp_path: Path, monkeypatch) -> None:
    """apply() renames current binary to .old.<ts> and installs new bytes.

    Uses tmp_path as the install root so this is filesystem-isolated and
    platform-agnostic. The orchestrator must NOT branch on sys.platform.
    """
    # Pin the binary filename to the Unix variant — the Windows variant
    # (#37) parameterizes this same test with "wbox.exe".
    monkeypatch.setattr(su, "_binary_name", lambda: "wbox")

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
# CLI smoke
# ---------------------------------------------------------------------------


def test_self_upgrade_help_renders(runner) -> None:
    """`wbox self upgrade --help` must render without exceptions."""
    result = runner.invoke(app, ["self", "upgrade", "--help"])
    assert result.exit_code == 0
    assert "upgrade" in result.stdout.lower()


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
