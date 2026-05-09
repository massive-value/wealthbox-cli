"""Self-upgrade orchestrator for the `wbox` CLI.

This is the Module B tracer (issue #32). The public surface is two
functions plus two dataclasses:

- ``check()`` queries the GitHub Releases API for the latest ``v*`` tag,
  compares to the installed ``__version__``, and returns a populated
  :class:`NewVersion` when an upgrade is available (otherwise ``None``).
- ``apply(version, install_root)`` downloads the platform-specific binary,
  verifies its SHA-256 against the release's ``SHA256SUMS.txt`` manifest,
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
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from wealthbox_tools import __version__

# Subprocess creation flags used by the Windows deferred-swap helper.
# Looked up via getattr so this module imports cleanly on POSIX (where the
# constants don't exist on the subprocess module). The actual values come
# from MSDN Process Creation Flags.
_DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
_CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)

__all__ = [
    "NewVersion",
    "ReleaseStaleness",
    "UpgradeResult",
    "check",
    "check_release_staleness",
    "apply",
    "_cleanup_stale_backups",
]

_RELEASES_LATEST_URL = (
    "https://api.github.com/repos/massive-value/wealthbox-cli/releases/latest"
)
_CHECKSUMS_ASSET_NAME = "SHA256SUMS.txt"
_HTTP_TIMEOUT = httpx.Timeout(30.0)

# Retention window for `<binary>.old.<unix_ts>` rollback breadcrumbs. After
# 24 hours the user has either rolled back manually or the upgrade is
# stable; the file is then disposable. Fixed by design (issue #39) — not
# a parameter, so behavior is identical between `apply()` and `wbox
# doctor` and there's no "policy" surface to diverge.
_BACKUP_RETENTION_SECONDS = 24 * 3600


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
class ReleaseStaleness:
    """Snapshot of latest-release metadata used by `wbox doctor` (#41).

    A `behind=True, days_old > 30` combination triggers the doctor's
    "30-days-behind" upgrade nudge. We carry both fields (rather than a
    pre-baked boolean) so the doctor can render an informative message.
    """

    latest_version: str
    behind: bool
    days_old: int
    published_at: datetime


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


def _perform_swap(current: Path, partial: Path, backup: Path) -> None:
    """Rename ``current`` → ``backup`` (if it exists) and ``partial`` → ``current``.

    The pure swap unit shared by the Unix in-process path and the Windows
    deferred-swap helper. Platform-uniform except for the Unix-only chmod
    that restores the execute bit (Windows has no execute-bit concept).

    The Unix-only chmod is needed because ``Path.open("wb")`` in
    :func:`_download` creates the partial with the process umask (typically
    ``0644``); without restoring ``0o755`` the upgraded binary would lose
    its execute bit and fail to run after upgrade.
    """
    if current.exists():
        os.replace(current, backup)
    if sys.platform != "win32":
        partial.chmod(0o755)
    os.replace(partial, current)


def _is_windows() -> bool:
    """Hook for the platform-policy dispatch in :func:`_schedule_swap`.

    Indirected (rather than reading ``sys.platform`` inline) so tests can
    exercise both branches against a Unix runner without monkeypatching
    ``sys.platform`` itself, which would also affect unrelated stdlib
    behavior (path separators, environment lookup, etc.).
    """
    return sys.platform == "win32"


def _schedule_swap(
    current: Path, partial: Path, backup: Path, parent_pid: int, version: str
) -> None:
    """Single platform-dispatch seam for the swap step in :func:`apply`.

    On Unix, runs :func:`_perform_swap` synchronously and returns. On
    Windows, the running ``wbox.exe`` is locked by the OS so the rename
    must be deferred to a child process that waits for the parent to exit.
    See :func:`_schedule_deferred_swap`. ``version`` flows through to the
    Windows helper so it can write the upgrade outcome to the status file.
    """
    if _is_windows():
        _schedule_deferred_swap(current, partial, backup, parent_pid, version)
    else:
        _perform_swap(current, partial, backup)


_STATUS_FILENAME = "wbox.upgrade.status"

# Marker file written by `apply()` on Windows after scheduling the deferred
# swap. The actual `wbox skills upgrade` subprocess can't run from the parent
# (the new binary isn't on disk yet — the helper renames it after parent
# exit), so the marker tells :func:`_check_pending_upgrade_status` to fire
# the subprocess once it confirms the deferred swap succeeded. On Unix the
# swap is synchronous, so :func:`apply` invokes the subprocess inline and
# this marker is never written.
_SKILLS_UPGRADE_PENDING_FILENAME = "wbox.skills_upgrade.pending"


def _invoke_skills_upgrade(binary_path: Path) -> int:
    """Run ``<binary_path> skills upgrade`` and stream output to the terminal.

    Returns the subprocess exit code. Output is intentionally NOT captured —
    we want the user to see template-refresh progress live. Errors during
    spawn (e.g., the binary disappeared between rename and exec) are caught
    and returned as a synthetic non-zero so the caller can warn without
    rolling back the binary swap; the binary is already in place and the
    user can re-run ``wbox skills upgrade`` manually.

    Indirected (rather than inlined into :func:`apply`) so tests can
    monkeypatch a single seam without simulating the full subprocess
    machinery.
    """
    try:
        completed = subprocess.run(
            [str(binary_path), "skills", "upgrade"],
            check=False,
        )
        return completed.returncode
    except OSError:
        return 1


def _read_and_clear_upgrade_status(install_root: Path) -> dict | None:
    """Read + clear the upgrade status file written by the Windows helper.

    Called on every CLI startup. Returns the parsed JSON dict if a status
    file is present and well-formed; ``None`` otherwise. Deletes the file
    in both the well-formed and malformed cases (the malformed file would
    otherwise nag the user every launch).

    Never raises: the caller is the root-callback hook in :mod:`cli.main`,
    where any exception would crash every ``wbox`` invocation until the
    user manually cleared the file.
    """
    status_path = install_root / _STATUS_FILENAME
    if not status_path.exists():
        return None
    try:
        data = json.loads(status_path.read_text())
    except (OSError, json.JSONDecodeError):
        try:
            status_path.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    try:
        status_path.unlink(missing_ok=True)
    except OSError:
        pass
    if not isinstance(data, dict):
        return None
    return data


def _ps_single_quote(s: str) -> str:
    """Wrap ``s`` in PowerShell single-quote string literal syntax.

    Inside a single-quoted PS string, ``''`` (two single quotes) is the
    only escape needed — backslashes, ``$``, and backticks are all literal.
    Used to embed Windows paths into the inline helper script safely.
    """
    return "'" + s.replace("'", "''") + "'"


def _build_powershell_command(
    parent_pid: int,
    current: Path,
    partial: Path,
    backup: Path,
    status_path: Path,
    version: str,
    timeout_seconds: int = 30,
) -> list[str]:
    """Build argv for ``subprocess.Popen`` to run the deferred-swap helper.

    The returned list is passed to Popen verbatim. The helper:

    1. Polls ``Get-Process -Id <parent_pid>`` every 100ms until the parent
       exits or ``timeout_seconds`` elapses.
    2. If the parent exited in time: retries the rename pair (current →
       backup, partial → current) for up to 3 seconds to absorb the brief
       window between process exit and OS file-lock release.
    3. Writes a JSON status file atomically (``.tmp`` + Move-Item) so the
       next ``wbox`` launch can surface the outcome.
    """
    cur_q = _ps_single_quote(str(current))
    par_q = _ps_single_quote(str(partial))
    bak_q = _ps_single_quote(str(backup))
    sta_q = _ps_single_quote(str(status_path))
    ver_q = _ps_single_quote(version)

    script = f"""\
$parentPid = {parent_pid}
$current = {cur_q}
$partial = {par_q}
$backup = {bak_q}
$statusPath = {sta_q}
$version = {ver_q}
$timeoutSeconds = {timeout_seconds}
$start = Get-Date
while (
    (Get-Process -Id $parentPid -ErrorAction SilentlyContinue) -and
    (((Get-Date) - $start).TotalSeconds -lt $timeoutSeconds)
) {{
    Start-Sleep -Milliseconds 100
}}
$ts = [int][double]::Parse((Get-Date -UFormat %s))
$status = @{{ result = ''; version = $version; reason = $null; ts = $ts }}
if (Get-Process -Id $parentPid -ErrorAction SilentlyContinue) {{
    $status.result = 'failed'
    $status.reason = 'timeout waiting for parent exit'
}}
else {{
    $swapped = $false
    for ($i = 0; $i -lt 30; $i++) {{
        try {{
            if (Test-Path -LiteralPath $current) {{
                Move-Item -LiteralPath $current -Destination $backup -Force
            }}
            Move-Item -LiteralPath $partial -Destination $current -Force
            $swapped = $true
            break
        }} catch {{
            Start-Sleep -Milliseconds 100
        }}
    }}
    $status.ts = [int][double]::Parse((Get-Date -UFormat %s))
    if ($swapped) {{
        $status.result = 'ok'
    }}
    else {{
        if ((Test-Path -LiteralPath $backup) -and (-not (Test-Path -LiteralPath $current))) {{
            try {{ Move-Item -LiteralPath $backup -Destination $current -Force }} catch {{ }}
        }}
        $status.result = 'failed'
        $status.reason = 'rename failed after retries'
    }}
}}
$statusJson = $status | ConvertTo-Json -Compress
$tmpStatus = $statusPath + '.tmp'
Set-Content -Path $tmpStatus -Value $statusJson -NoNewline
Move-Item -LiteralPath $tmpStatus -Destination $statusPath -Force
"""

    return [
        "powershell",
        "-NoProfile",
        "-WindowStyle", "Hidden",
        "-Command", script,
    ]


def _schedule_deferred_swap(
    current: Path, partial: Path, backup: Path, parent_pid: int, version: str
) -> None:
    """Spawn a detached PowerShell helper to perform the swap after parent exit.

    The detached creation flags (DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP)
    plus DEVNULL stdio ensure the helper survives the parent's exit; without
    them the helper would inherit the parent's console and die with it.
    """
    status_path = current.with_name(_STATUS_FILENAME)
    argv = _build_powershell_command(
        parent_pid=parent_pid,
        current=current,
        partial=partial,
        backup=backup,
        status_path=status_path,
        version=version,
    )
    subprocess.Popen(
        argv,
        creationflags=_DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )


def _cleanup_stale_backups(
    install_root: Path, *, now: float | None = None
) -> list[Path]:
    """Remove ``<binary>.old.<unix_ts>`` files older than 24 h.

    Sweeps the install directory for rollback breadcrumbs left by prior
    successful :func:`apply` calls and unlinks any whose timestamp is
    older than :data:`_BACKUP_RETENTION_SECONDS` relative to ``now``
    (default: ``time.time()``). Returns the list of paths actually
    removed so callers (``wbox doctor``) can report the count.

    Defensive: a file whose trailing component cannot be parsed as an
    integer is left alone — we never want a typo / unrelated
    ``.old.something`` to be deleted by surprise.
    """
    install_root = Path(install_root)
    cutoff = (now if now is not None else time.time()) - _BACKUP_RETENTION_SECONDS
    pattern = f"{_binary_name()}.old.*"
    removed: list[Path] = []
    for path in install_root.glob(pattern):
        suffix = path.name.rsplit(".", 1)[-1]
        try:
            ts = int(suffix)
        except ValueError:
            continue
        if ts < cutoff:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                # Stale handle / permission issue — best effort, the
                # next sweep will retry.
                continue
            removed.append(path)
    return removed


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


def check_release_staleness(*, now: datetime | None = None) -> ReleaseStaleness | None:
    """Return release-staleness metadata for `wbox doctor` (#41).

    Hits the same GitHub Releases endpoint as :func:`check`, but returns a
    :class:`ReleaseStaleness` snapshot (latest tag, whether the running
    version is older, age in days) instead of an upgrade candidate. The
    doctor uses this to nudge users who are >30 days behind the latest
    release.

    Returns ``None`` for any soft failure: network error, missing or
    malformed ``published_at``, missing tag. The doctor renders these as
    "could not check for updates" rather than failing the run. We
    deliberately do NOT raise — this is a courtesy check, not a gate.
    """
    try:
        response = httpx.get(
            _RELEASES_LATEST_URL,
            timeout=_HTTP_TIMEOUT,
            headers={"Accept": "application/vnd.github+json"},
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        # Doctor must never crash on a soft network check — catch broadly
        # so transport errors, JSON decode failures, and unmocked-endpoint
        # AssertionErrors in tests all render as "could not check for
        # updates" instead of propagating.
        return None

    tag = payload.get("tag_name") or ""
    if not tag:
        return None

    latest = _parse_version(tag)
    current = _parse_version(_running_version())
    behind = bool(latest) and latest > current

    published_raw = payload.get("published_at")
    if not isinstance(published_raw, str) or not published_raw:
        return None
    try:
        # GitHub returns RFC 3339 with a trailing "Z"; normalize for fromisoformat.
        published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    reference = now if now is not None else datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    days_old = max(0, (reference - published_at).days)

    return ReleaseStaleness(
        latest_version=tag.lstrip("vV"),
        behind=behind,
        days_old=days_old,
        published_at=published_at,
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

        _schedule_swap(
            current_path, partial_path, backup_path, os.getpid(), version.version
        )
    except BaseException:
        # Best-effort cleanup of the partial download. Do NOT touch the
        # backup — if step 3 succeeded but step 4 failed the user still
        # needs the breadcrumb to recover.
        try:
            partial_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    # Refresh the agent skill template in lockstep with the new binary (#40).
    # On Unix the swap is synchronous, so we invoke `<new wbox> skills upgrade`
    # right here. On Windows the swap is deferred to a child process that runs
    # after the parent exits; we drop a marker file and let the next-launch
    # callback fire the subprocess once it has confirmed the swap succeeded.
    # A non-zero exit is a warning, never a rollback — the binary is already
    # in place and the user can re-run `wbox skills upgrade` manually.
    if _is_windows():
        try:
            (install_root / _SKILLS_UPGRADE_PENDING_FILENAME).write_text("")
        except OSError:
            pass
    else:
        try:
            rc = _invoke_skills_upgrade(current_path)
        except Exception:
            rc = 1
        if rc != 0:
            # Surface to the user; the parent process is still alive on Unix
            # so this lands on the active terminal.
            print(
                f"warning: `wbox skills upgrade` exited with code {rc}; "
                "the binary swap is intact. Re-run manually to refresh the "
                "skill template.",
                file=sys.stderr,
            )

    # Sweep stale `.old.<ts>` breadcrumbs from prior successful upgrades
    # (#39). Only runs on success — on failure the freshly-renamed
    # backup IS the recovery path, and we don't want to risk the sweep
    # catching it via a clock skew. Best-effort: any error here is
    # swallowed because the upgrade itself succeeded.
    try:
        _cleanup_stale_backups(install_root)
    except OSError:
        pass

    return UpgradeResult(
        version=version.version,
        installed_path=current_path,
        backup_path=backup_path,
    )
