"""Read-only diff between an :class:`~.archive.ImportPlan` and a firm directory.

``firm diff`` (issue #47) reuses :func:`~.archive.unpack` to read the
archive, then walks the resulting plan + firm directory and produces a
unified-diff per changed file. Nothing is written; the firm dir is
read-only here.

``_meta.json`` is intentionally excluded from the diff. Pack strips it to
the policy-key subset (``META_POLICY_KEYS``) and apply merges that subset
into the destination — a bytewise diff would always show drift between the
archive's stripped meta and the destination's merged meta even when the
firm and the archive are in lockstep on policy. Skipping the file
sidesteps that false-positive without giving up anything we'd notice in
practice (the only policy key today is ``onboarded_at``, which doesn't
benefit from a per-line diff). If a future schema makes per-key meta diff
useful, swap this for the META_POLICY_KEYS subset diff (Option B in the
issue brief).
"""
from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path

from .archive import HAND_EDITED_FILES, META_FILENAME, ImportPlan


@dataclass(frozen=True)
class DiffEntry:
    """A single per-file unified diff."""

    name: str
    body: str  # the unified-diff text, may be empty when there's no body to show


@dataclass(frozen=True)
class DiffReport:
    """The result of comparing an :class:`ImportPlan` against a firm directory.

    Buckets are mutually exclusive: a file appears in exactly one of
    ``added``/``modified``/``removed``. ``has_changes`` is true if any
    bucket is non-empty — callers use it to set the process exit code so
    ``firm diff`` is pipe-checkable.
    """

    added: tuple[str, ...] = ()
    modified: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()
    diffs: tuple[DiffEntry, ...] = field(default_factory=tuple)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.removed)


def compute_diff(plan: ImportPlan, firm_dir: Path) -> DiffReport:
    """Compute the per-file diff between ``plan`` and ``firm_dir``.

    "Added" = in plan, not on disk. "Modified" = both sides have it but
    the bytes differ (after line-ending normalization — see below).
    "Removed" = on disk under ``firm_dir`` (within the hand-edited
    whitelist), not in the plan. Removed is conceptual — the archive
    doesn't carry the file, so a subsequent overwrite-mode import
    wouldn't re-create it; the diff command never deletes anything.

    Line endings are normalized to ``\\n`` on both sides before comparison
    because ``pack`` stores files with whatever line endings they had on
    disk and zip storage is byte-for-byte, but the destination on disk
    may have ``\\r\\n`` (Windows) or ``\\n`` (Unix) depending on the host.
    Without normalization every file would surface as "modified" on
    Windows even when the content is in lockstep.

    ``_meta.json`` is excluded from the comparison — see module docstring.
    """
    firm_dir = Path(firm_dir)

    # Plan side: every entry except _meta.json. Anything outside the
    # hand-edited whitelist is impossible by construction (unpack rejects
    # it), but we still filter defensively rather than trust the plan.
    plan_files: dict[str, bytes] = {
        name: _normalize_eol(blob)
        for name, blob in plan.files.items()
        if name != META_FILENAME and name in HAND_EDITED_FILES
    }

    # Disk side: only inspect the hand-edited whitelist. Generated files
    # (categories.md, custom-fields.md, users.md) live in firm_dir but are
    # not policy — they don't travel with the archive and reporting them
    # as "removed" would be misleading noise.
    disk_files: dict[str, bytes] = {}
    if firm_dir.is_dir():
        for name in HAND_EDITED_FILES:
            target = firm_dir / name
            if target.is_file() and not target.is_symlink():
                disk_files[name] = _normalize_eol(target.read_bytes())

    added: list[str] = []
    modified: list[str] = []
    removed: list[str] = []
    diffs: list[DiffEntry] = []

    plan_names = set(plan_files)
    disk_names = set(disk_files)

    for name in sorted(plan_names | disk_names):
        in_plan = name in plan_files
        in_disk = name in disk_files
        if in_plan and not in_disk:
            added.append(name)
            diffs.append(
                DiffEntry(
                    name=name,
                    body=_unified(b"", plan_files[name], a_label=name, b_label=name),
                )
            )
        elif in_disk and not in_plan:
            removed.append(name)
            diffs.append(
                DiffEntry(
                    name=name,
                    body=_unified(disk_files[name], b"", a_label=name, b_label=name),
                )
            )
        else:
            disk_blob = disk_files[name]
            plan_blob = plan_files[name]
            if disk_blob == plan_blob:
                continue
            modified.append(name)
            diffs.append(
                DiffEntry(
                    name=name,
                    body=_unified(disk_blob, plan_blob, a_label=name, b_label=name),
                )
            )

    return DiffReport(
        added=tuple(added),
        modified=tuple(modified),
        removed=tuple(removed),
        diffs=tuple(diffs),
    )


def _normalize_eol(blob: bytes) -> bytes:
    """Collapse ``\\r\\n`` and lone ``\\r`` to ``\\n``.

    Used by :func:`compute_diff` so a Windows checkout (CRLF on disk)
    matches a zip-stored body (LF) when the textual content is identical.
    """
    return blob.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _unified(a: bytes, b: bytes, *, a_label: str, b_label: str) -> str:
    """Return the unified-diff body for ``a`` vs ``b``.

    Bytes are decoded as UTF-8 with ``errors="replace"`` so a stray binary
    payload doesn't crash the diff (the archive whitelist makes binaries
    unlikely, but defensiveness costs nothing here).

    Files that don't end with ``\\n`` cause ``difflib.unified_diff`` to emit
    ``-``/``+`` records without terminators; joining those verbatim
    concatenates lines (``-old+new``) and corrupts the next file header.
    Append a git-style ``\\ No newline at end of file`` marker after any
    such record so the output stays parseable as unified diff.
    """
    a_text = a.decode("utf-8", errors="replace").splitlines(keepends=True)
    b_text = b.decode("utf-8", errors="replace").splitlines(keepends=True)
    lines = difflib.unified_diff(
        a_text,
        b_text,
        fromfile=f"a/{a_label}",
        tofile=f"b/{b_label}",
        n=3,
    )
    return "".join(_terminate(line) for line in lines)


def _terminate(line: str) -> str:
    """Ensure a unified-diff line ends with ``\\n``.

    Adds the git ``\\ No newline at end of file`` marker after content
    lines (``-`` / ``+`` / ` `) that lack a terminator. Header lines
    (``---``, ``+++``, ``@@``) always come from ``difflib`` already
    terminated and pass through unchanged.
    """
    if line.endswith("\n"):
        return line
    return line + "\n\\ No newline at end of file\n"


def format_report(report: DiffReport) -> str:
    """Render a :class:`DiffReport` as text suitable for ``stdout``.

    Layout::

        Added (1):
          contacts.md
        Modified (2):
          tasks.md
          notes.md
        Removed (1):
          events.md

        --- a/contacts.md
        +++ b/contacts.md
        @@ ... @@
        ...

    When the report has no changes, returns ``"No changes.\\n"`` so the
    caller can still echo *something* to stdout — handy when piping.
    """
    if not report.has_changes:
        return "No changes.\n"

    lines: list[str] = []
    if report.added:
        lines.append(f"Added ({len(report.added)}):")
        lines.extend(f"  {n}" for n in report.added)
    if report.modified:
        lines.append(f"Modified ({len(report.modified)}):")
        lines.extend(f"  {n}" for n in report.modified)
    if report.removed:
        lines.append(f"Removed ({len(report.removed)}):")
        lines.extend(f"  {n}" for n in report.removed)

    out = "\n".join(lines) + "\n"
    bodies = [d.body for d in report.diffs if d.body]
    if bodies:
        out += "\n" + "".join(bodies)
        if not out.endswith("\n"):
            out += "\n"
    return out
