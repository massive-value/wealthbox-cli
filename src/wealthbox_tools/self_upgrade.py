"""Self-upgrade orchestrator for the `wbox` CLI.

This is the Module B tracer (issue #32). The public surface is two
functions plus two dataclasses:

- ``check()`` queries the GitHub Releases API for the latest ``v*`` tag,
  compares to the installed ``__version__``, and returns a populated
  :class:`NewVersion` when an upgrade is available (otherwise ``None``).
- ``apply(version, install_root)`` downloads the platform-specific binary,
  verifies its SHA-256 against the release's ``checksums.txt`` manifest,
  and atomically swaps it into place. The previous binary is preserved
  under a ``.old.<unix_ts>`` breadcrumb for rollback / future cleanup
  (issue #39).

Design constraint (#37): the orchestrator body must be **platform-uniform**
so the Windows test can parameterize cleanly. The only platform check
lives inside :func:`_binary_name`, which is the single point of
parameterization. We use :func:`os.replace` (atomic on both POSIX and
Windows) and :class:`pathlib.Path` for all path manipulation, and we
download into the same directory as the install target so the rename is
guaranteed atomic (no cross-device fallback to copy-then-delete).
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from wealthbox_tools import __version__

__all__ = [
    "NewVersion",
    "UpgradeResult",
    "check",
    "apply",
]

_RELEASES_LATEST_URL = (
    "https://api.github.com/repos/massive-value/wealthbox-cli/releases/latest"
)
_CHECKSUMS_ASSET_NAME = "checksums.txt"
_HTTP_TIMEOUT = httpx.Timeout(30.0)


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NewVersion:
    """An upgrade candidate surfaced by :func:`check`."""

    version: str
    binary_url: str
    sha256: str
    asset_name: str


@dataclass(frozen=True)
class UpgradeResult:
    """The outcome of a successful :func:`apply` call."""

    version: str
    installed_path: Path
    backup_path: Path


# ---------------------------------------------------------------------------
# Small helpers — the only places allowed to touch platform / global state.
# Tests monkeypatch these to parameterize without touching the orchestrator.
# ---------------------------------------------------------------------------


def _binary_name() -> str:
    """Filename of the running CLI binary on the current OS.

    The single platform-aware helper. The orchestrator must NOT branch on
    ``sys.platform`` directly — call this instead.
    """
    return "wbox.exe" if sys.platform == "win32" else "wbox"


def _asset_name_for_platform() -> str:
    """Release asset filename matching the current OS/arch.

    Conservative defaults for the tracer; richer arch detection lives in
    sibling issues. Tests monkeypatch this to pin a deterministic asset.
    """
    if sys.platform == "win32":
        return "wbox-windows-x64.exe"
    if sys.platform == "darwin":
        return "wbox-macos-x64"
    return "wbox-linux-x64"


def _running_version() -> str:
    """Version of the running CLI. Indirected so tests can pin a value."""
    return __version__


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_version(tag_or_version: str) -> tuple[int, ...]:
    """Parse a SemVer-ish version string into a tuple for comparison.

    Strips a leading ``v``. Non-numeric pre-release suffixes are dropped.
    """
    raw = tag_or_version.lstrip("vV").strip()
    # Drop pre-release / build metadata for the tracer comparison.
    for sep in ("-", "+"):
        if sep in raw:
            raw = raw.split(sep, 1)[0]
    parts: list[int] = []
    for piece in raw.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _select_asset(assets: list[dict], wanted_name: str) -> dict | None:
    for asset in assets:
        if asset.get("name") == wanted_name:
            return asset
    return None


def _parse_checksums(body: str, target_name: str) -> str | None:
    """Parse a sha256sum-style manifest and return the digest for ``target_name``.

    Each line is ``<hex-digest>  <filename>`` (two spaces, per ``sha256sum``)
    but we tolerate any whitespace separator.
    """
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, name = parts[0], parts[1].lstrip("*").strip()
        if name == target_name:
            return digest.lower()
    return None


def _download(url: str, dest: Path) -> None:
    """Stream ``url`` to ``dest``. Caller is responsible for cleanup on error."""
    with httpx.stream("GET", url, timeout=_HTTP_TIMEOUT, follow_redirects=True) as response:
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_bytes():
                fh.write(chunk)


def _verify_sha256(path: Path, expected_hex: str) -> None:
    """Raise :class:`ChecksumMismatchError` if ``path`` does not match ``expected_hex``.

    Isolated so #38's regression test can drive it directly.
    """
    actual = hashlib.sha256(path.read_bytes()).hexdigest().lower()
    if actual != expected_hex.lower():
        raise ChecksumMismatchError(
            f"SHA-256 mismatch for {path.name}: expected {expected_hex}, got {actual}"
        )


class ChecksumMismatchError(RuntimeError):
    """Raised by :func:`_verify_sha256` when the downloaded bytes are wrong."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check() -> NewVersion | None:
    """Return an :class:`NewVersion` if an upgrade is available, else ``None``."""
    response = httpx.get(
        _RELEASES_LATEST_URL,
        timeout=_HTTP_TIMEOUT,
        headers={"Accept": "application/vnd.github+json"},
    )
    response.raise_for_status()
    payload = response.json()

    tag = payload.get("tag_name") or ""
    latest = _parse_version(tag)
    current = _parse_version(_running_version())
    if not latest or latest <= current:
        return None

    assets = payload.get("assets") or []
    wanted_asset_name = _asset_name_for_platform()
    binary_asset = _select_asset(assets, wanted_asset_name)
    checksums_asset = _select_asset(assets, _CHECKSUMS_ASSET_NAME)
    if binary_asset is None or checksums_asset is None:
        return None

    checksums_url = checksums_asset["browser_download_url"]
    cs_resp = httpx.get(checksums_url, timeout=_HTTP_TIMEOUT, follow_redirects=True)
    cs_resp.raise_for_status()
    digest = _parse_checksums(cs_resp.text, wanted_asset_name)
    if digest is None:
        return None

    return NewVersion(
        version=tag.lstrip("vV"),
        binary_url=binary_asset["browser_download_url"],
        sha256=digest,
        asset_name=wanted_asset_name,
    )


def apply(version: NewVersion, install_root: Path) -> UpgradeResult:
    """Install ``version`` into ``install_root``, returning a result breadcrumb.

    Sequence (platform-uniform):

    1. Download the new binary to ``install_root / wbox.partial.<ts>``.
    2. Verify SHA-256 against ``version.sha256``.
    3. Atomically rename current binary to ``wbox.old.<ts>`` (breadcrumb).
    4. Atomically rename partial download to the install target.

    The download lands in the SAME directory as the target so step 4 is a
    same-filesystem :func:`os.replace`, which is atomic on both POSIX and
    Windows. Crucially we do NOT use :func:`shutil.move` (would fall back
    to copy+delete across filesystems) or :func:`os.rename` (raises on
    Windows when the target already exists).
    """
    install_root = Path(install_root)
    binary_filename = _binary_name()
    current_path = install_root / binary_filename

    ts = int(time.time())
    partial_path = install_root / f"{binary_filename}.partial.{ts}"
    backup_path = current_path.with_name(f"{binary_filename}.old.{ts}")

    try:
        _download(version.binary_url, partial_path)
        _verify_sha256(partial_path, version.sha256)

        if current_path.exists():
            os.replace(current_path, backup_path)
        # Codex P1: ensure the new binary is executable on Unix/macOS.
        # `Path.open("wb")` in `_download` creates the partial with the
        # process umask (typically 0644), which would strip the execute
        # bit and make the upgraded `wbox` un-runnable until manual
        # `chmod`. Confined to non-Windows because Windows has no
        # execute-bit concept; the orchestrator stays branch-free
        # everywhere else.
        if sys.platform != "win32":
            partial_path.chmod(0o755)
        os.replace(partial_path, current_path)
    except BaseException:
        # Best-effort cleanup of the partial download. Do NOT touch the
        # backup — if step 3 succeeded but step 4 failed the user still
        # needs the breadcrumb to recover.
        try:
            partial_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    return UpgradeResult(
        version=version.version,
        installed_path=current_path,
        backup_path=backup_path,
    )
