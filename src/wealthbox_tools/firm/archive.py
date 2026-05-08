"""Firm-archive packing and unpacking.

Produces a portable zip of a firm directory's hand-edited policy files plus
a small manifest, and applies such an archive back onto a firm directory.
The pack contract is **whitelist-only**: ``pack`` copies only the explicitly
listed files into the archive — anything else in the source ``firm_dir`` is
silently dropped. This makes it impossible for generated files
(``categories.md``, ``custom-fields.md``, ``users.md``), API-derived
``_meta.json`` fields (refresh timestamps, ``cli_version``), or ad-hoc
debris in the firm directory to leak into the export.

The user preferences directory (``~/.config/wbox/user/``) is never reachable
from this module by construction: ``pack`` only sees ``firm_dir``.

Apply modes (overwrite, merge, abort-on-conflict) are exposed as
:class:`ApplyMode`, but only ``OVERWRITE`` is implemented in the current
slice — ``MERGE`` and ``ABORT_ON_CONFLICT`` exist as enum values so future
slices (#46) can wire their behavior in without breaking the public surface.
"""
from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
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


#: Manifest filename inside the archive.
MANIFEST_NAME = ".manifest.json"

#: Filename of the per-firm metadata document. ``pack`` only includes the
#: policy subset of this file (currently just ``onboarded_at``); ``apply``
#: therefore merges that subset into the destination's existing meta rather
#: than overwriting it, so generated keys (``identity``, ``cli_version``,
#: ``files`` timestamps) that ``wbox doctor`` relies on survive.
META_FILENAME = "_meta.json"


class ArchiveError(Exception):
    """Raised when an archive cannot be unpacked or applied."""


class ApplyMode(StrEnum):
    """How :func:`apply` reconciles archive contents with the firm directory.

    Only ``OVERWRITE`` is implemented in the current slice (#36). ``MERGE``
    and ``ABORT_ON_CONFLICT`` are placeholders that #46 will wire up against
    the same :func:`apply` surface.
    """

    OVERWRITE = "overwrite"
    MERGE = "merge"
    ABORT_ON_CONFLICT = "abort-on-conflict"


def _is_safe_archive_name(name: str) -> bool:
    """Return ``True`` if ``name`` is safe to write under a target directory.

    Rejects path-traversal (``..``), current-dir aliases (``.``), absolute
    paths, Windows drive letters, backslashes, directory entries (trailing
    slash), and empty path components. Anything that survives this check
    can be safely joined onto ``firm_dir`` and written as a regular file.

    ``.`` matters specifically because ``firm_dir / "."`` resolves to
    ``firm_dir`` itself; ``write_bytes`` on a directory raises
    ``IsADirectoryError``, which would bypass the CLI's clean-error path.
    Trailing-slash directory entries have the same failure mode.
    """
    if not name:
        return False
    if "\\" in name:
        return False
    if name.startswith("/"):
        return False
    if name.endswith("/"):
        return False
    if len(name) >= 2 and name[1] == ":":
        return False
    parts = name.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return False
    return True


@dataclass(frozen=True)
class ImportPlan:
    """The contents of a successfully-unpacked archive, ready to apply.

    ``manifest`` is the parsed ``.manifest.json``. ``files`` maps each
    archive entry's relative path to its raw bytes — keeping bytes (not
    str) means future binary entries pass through unchanged.
    """

    manifest: dict[str, Any]
    files: dict[str, bytes] = field(default_factory=dict)


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of an :func:`apply` invocation."""

    written: tuple[str, ...]


def unpack(source: Path | str) -> ImportPlan:
    """Read a firm-archive zip from disk and return its :class:`ImportPlan`.

    URL fetch is deferred to issue #45; ``source`` is treated as a local
    filesystem path for now.

    Raises:
        ArchiveError: the file isn't a valid zip, the manifest is missing
            or malformed, or the manifest's ``format_version`` is newer
            than this CLI understands.
    """
    path = Path(source)
    try:
        with zipfile.ZipFile(path, mode="r") as zf:
            try:
                manifest_raw = zf.read(MANIFEST_NAME)
            except KeyError as exc:
                raise ArchiveError(
                    f"{path}: archive is missing {MANIFEST_NAME}; not a firm archive."
                ) from exc
            entry_names = [n for n in zf.namelist() if n != MANIFEST_NAME]
            for entry in entry_names:
                if not _is_safe_archive_name(entry):
                    raise ArchiveError(
                        f"{path}: archive contains unsafe entry path {entry!r}; "
                        "refusing to import."
                    )
            files = {name: zf.read(name) for name in entry_names}
    except zipfile.BadZipFile as exc:
        raise ArchiveError(f"{path}: not a valid zip archive.") from exc
    except FileNotFoundError as exc:
        raise ArchiveError(f"{path}: archive file not found.") from exc
    except OSError as exc:
        raise ArchiveError(f"{path}: cannot read archive: {exc}") from exc

    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ArchiveError(f"{path}: {MANIFEST_NAME} is not valid JSON.") from exc
    if not isinstance(manifest, dict):
        raise ArchiveError(f"{path}: {MANIFEST_NAME} must be a JSON object.")

    version = manifest.get("format_version")
    if not isinstance(version, int) or version > FORMAT_VERSION:
        raise ArchiveError(
            f"{path}: unsupported format_version {version!r}. "
            f"This CLI understands format_version up to {FORMAT_VERSION}; "
            "upgrade `wealthbox-cli` to read this archive."
        )

    return ImportPlan(manifest=manifest, files=files)


def apply(
    plan: ImportPlan,
    firm_dir: Path,
    mode: ApplyMode = ApplyMode.OVERWRITE,
) -> ApplyResult:
    """Write the files from ``plan`` into ``firm_dir`` according to ``mode``.

    In ``OVERWRITE`` mode every file in the plan is written unconditionally;
    files already in ``firm_dir`` that are not in the plan are left alone
    (the archive is whitelist-only, so generated files like
    ``categories.md`` survive untouched on the destination).

    ``MERGE`` and ``ABORT_ON_CONFLICT`` are not implemented in this slice
    and raise :class:`ArchiveError`. Issue #46 will fill them in.
    """
    if mode is not ApplyMode.OVERWRITE:
        raise ArchiveError(
            f"apply mode {mode.value!r} is not implemented yet; only "
            f"{ApplyMode.OVERWRITE.value!r} is supported in this release."
        )

    firm_dir = Path(firm_dir)
    firm_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for name, content in plan.files.items():
        if not _is_safe_archive_name(name):
            raise ArchiveError(
                f"plan contains unsafe entry path {name!r}; refusing to write."
            )
        target = firm_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if name == META_FILENAME:
            content = _merge_meta_bytes(target, content)
        target.write_bytes(content)
        written.append(name)
    return ApplyResult(written=tuple(written))


def _merge_meta_bytes(target: Path, incoming: bytes) -> bytes:
    """Merge the archive's ``_meta.json`` policy subset into the existing one.

    ``pack`` only stores policy-shaped keys in ``_meta.json``. Wholesale
    overwrite would delete generated keys (``identity``, ``cli_version``,
    ``files``) that survive on the destination side. We merge the incoming
    keys on top of the existing document so policy values come from the
    archive while generated values persist locally. If either document is
    missing or malformed, we fall back to writing the incoming bytes
    verbatim — the same behavior as before the merge was introduced.
    """
    try:
        incoming_obj = json.loads(incoming.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return incoming
    if not isinstance(incoming_obj, dict) or not target.exists():
        return incoming
    try:
        existing_obj = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return incoming
    if not isinstance(existing_obj, dict):
        return incoming
    merged = {**existing_obj, **incoming_obj}
    return (json.dumps(merged, indent=2) + "\n").encode("utf-8")


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
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2) + "\n")
        if meta_policy:
            zf.writestr("_meta.json", json.dumps(meta_policy, indent=2) + "\n")
        for name in HAND_EDITED_FILES:
            src = firm_dir / name
            if src.is_symlink() or not src.is_file():
                continue
            zf.writestr(name, src.read_text(encoding="utf-8"))
    return buf.getvalue()
