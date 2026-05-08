"""Firm-archive packing.

Produces a portable zip of a firm directory's hand-edited policy files plus
a small manifest. The contract is **whitelist-only**: ``pack`` copies only
the explicitly listed files into the archive — anything else in the source
``firm_dir`` is silently dropped. This makes it impossible for generated
files (``categories.md``, ``custom-fields.md``, ``users.md``), API-derived
``_meta.json`` fields (refresh timestamps, ``cli_version``), or ad-hoc
debris in the firm directory to leak into the export.

The user preferences directory (``~/.config/wbox/user/``) is never reachable
from this module by construction: ``pack`` only sees ``firm_dir``.
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Any

#: Manifest schema version. Bump on backwards-incompatible changes.
FORMAT_VERSION = 1

#: Hand-edited firm-policy markdown files that are included in the archive.
#: This is the canonical whitelist — adding a new resource here is a
#: deliberate, reviewable change.
HAND_EDITED_FILES: tuple[str, ...] = (
    "contacts.md",
    "tasks.md",
    "notes.md",
    "events.md",
    "opportunities.md",
    "projects.md",
    "workflows.md",
)

#: The ``_meta.json`` keys that survive the pack. Anything else (identity
#: cache, ``cli_version``, per-file refresh timestamps) is API-derived and
#: regenerated on import; it must not travel with the archive.
META_POLICY_KEYS: tuple[str, ...] = ("onboarded_at",)


def _cli_version() -> str:
    try:
        return _pkg_version("wealthbox-cli")
    except PackageNotFoundError:
        # The package is always installed in normal use; fall back to a
        # sentinel so tests in unusual environments still get a manifest.
        return "0+unknown"


def _read_meta_policy(firm_dir: Path) -> tuple[dict[str, Any], str | None]:
    """Return ``(policy_subset, source_firm_name)`` from ``_meta.json``.

    The subset contains only :data:`META_POLICY_KEYS`. ``source_firm_name``
    is read out of the (otherwise discarded) ``identity`` block so the
    manifest can record it without leaking the rest of the cache.
    """
    meta_path = firm_dir / "_meta.json"
    if not meta_path.exists():
        return {}, None
    try:
        loaded = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}, None
    if not isinstance(loaded, dict):
        return {}, None

    policy: dict[str, Any] = {k: loaded[k] for k in META_POLICY_KEYS if k in loaded}
    identity = loaded.get("identity")
    source_firm_name: str | None = None
    if isinstance(identity, dict):
        name = identity.get("name")
        if isinstance(name, str):
            source_firm_name = name
    return policy, source_firm_name


def _build_manifest(
    *,
    exported_at: datetime,
    source_firm_name: str | None,
) -> dict[str, Any]:
    return {
        "format_version": FORMAT_VERSION,
        "exported_at": exported_at.isoformat(),
        "source_firm_name": source_firm_name,
        "source_cli_version": _cli_version(),
    }


def pack(firm_dir: Path, *, now: datetime | None = None) -> bytes:
    """Pack a firm directory into a zip blob.

    Only the whitelisted hand-edited markdown files (:data:`HAND_EDITED_FILES`)
    and the policy-shaped subset of ``_meta.json`` (:data:`META_POLICY_KEYS`)
    are copied into the archive. Missing files are skipped silently — a firm
    that has not yet authored a particular policy doc still produces a valid
    archive.

    Args:
        firm_dir: Source firm directory (e.g. ``~/.config/wbox/firm``).
        now: Override the ``exported_at`` timestamp. Defaults to
            ``datetime.now(timezone.utc)``. Tests use this to pin output for
            deterministic byte comparisons.

    Returns:
        The zip archive as raw bytes.
    """
    firm_dir = Path(firm_dir)
    exported_at = now if now is not None else datetime.now(timezone.utc)

    meta_policy, source_firm_name = _read_meta_policy(firm_dir)
    manifest = _build_manifest(
        exported_at=exported_at,
        source_firm_name=source_firm_name,
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".manifest.json", json.dumps(manifest, indent=2) + "\n")
        if meta_policy:
            zf.writestr("_meta.json", json.dumps(meta_policy, indent=2) + "\n")
        for name in HAND_EDITED_FILES:
            src = firm_dir / name
            if not src.is_file():
                continue
            zf.writestr(name, src.read_text(encoding="utf-8"))
    return buf.getvalue()
