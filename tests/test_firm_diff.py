"""Tests for ``wbox firm diff`` — read-only unified-diff against the firm dir.

Issue #47. ``firm diff`` reuses :func:`unpack` from ``firm.archive`` so the
same path/URL surface as ``firm import`` is honored. Output is a summary
header listing added / modified / removed files plus per-file unified
diffs. Exit code is ``0`` when nothing differs and non-zero otherwise so
callers can pipe-check.

``_meta.json`` is intentionally skipped from the per-file diff because the
archive carries only the policy-key subset (``META_POLICY_KEYS``) and apply
merges that subset into the destination — a bytewise diff would always
report drift even when the firm is in lockstep with the archive.
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from wealthbox_tools.cli.main import app
from wealthbox_tools.firm.archive import pack

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


_PINNED_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _populated_firm_dir(root: Path) -> dict[str, str]:
    """Create a firm dir with the same shape used by the import-side tests."""
    root.mkdir(parents=True, exist_ok=True)
    bodies = {
        "contacts.md": "# Contacts policy\n\nUse household-first onboarding.\n",
        "tasks.md": "# Tasks policy\n\nDefault priority is medium.\n",
        "notes.md": "# Notes policy\n",
        "events.md": "# Events policy\n",
        "opportunities.md": "# Opportunities policy\n",
        "projects.md": "# Projects policy\n",
        "workflows.md": "# Workflows policy\n",
    }
    for name, body in bodies.items():
        (root / name).write_text(body, encoding="utf-8")
    (root / "_meta.json").write_text(
        json.dumps({"onboarded_at": "2024-02-15T12:34:56+00:00"}, indent=2),
        encoding="utf-8",
    )
    return bodies


def _zip_with_manifest(
    path: Path,
    manifest: dict,
    bodies: dict[str, str] | None = None,
) -> Path:
    """Hand-craft a zip archive with the given manifest and optional file bodies."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".manifest.json", json.dumps(manifest, indent=2) + "\n")
        for name, body in (bodies or {}).items():
            zf.writestr(name, body)
    path.write_bytes(buf.getvalue())
    return path


# --------------------------------------------------------------------------- #
# Identical zip — empty change list, exit 0                                    #
# --------------------------------------------------------------------------- #


def test_firm_diff_identical_zip_reports_no_changes(runner, tmp_path: Path) -> None:
    """When the firm dir matches the archive byte-for-byte, ``firm diff``
    prints an empty change list and exits ``0`` so it's pipe-checkable."""
    from wealthbox_tools.cli._skill_paths import firm_dir

    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)
    for name, body in bodies.items():
        (fd / name).write_text(body, encoding="utf-8")

    result = runner.invoke(app, ["firm", "diff", str(archive)])

    assert result.exit_code == 0, result.stdout
    combined = (result.stdout or "") + (result.stderr or "")
    # No per-file diff bodies — at most a "no changes" summary line.
    assert "@@" not in combined
    assert "Traceback" not in combined


# --------------------------------------------------------------------------- #
# Mixed changes — added / modified / removed all surface                       #
# --------------------------------------------------------------------------- #


def test_firm_diff_mixed_changes_surface_in_summary_and_unified_diff(
    runner, tmp_path: Path
) -> None:
    """Added + modified + removed files show up in the summary header and the
    per-file unified diffs match the unified-diff format that callers can
    feed into ``patch`` etc.

    Setup:
      - archive has contacts.md (NEW vs disk), tasks.md (modified vs disk),
        notes.md (modified vs disk).
      - firm dir has tasks.md (older), notes.md (older), events.md (REMOVED:
        on disk only, not in archive).
    """
    from wealthbox_tools.cli._skill_paths import firm_dir

    # Build an archive with three of the seven hand-edited files.
    src = tmp_path / "src"
    src.mkdir()
    archive_bodies = {
        "contacts.md": "# Contacts policy\n\nUse household-first onboarding.\n",
        "tasks.md": "# Tasks policy\n\nDefault priority is HIGH.\n",
        "notes.md": "# Notes policy\n\nAlways link to the household.\n",
    }
    for name, body in archive_bodies.items():
        (src / name).write_text(body, encoding="utf-8")
    (src / "_meta.json").write_text(
        json.dumps({"onboarded_at": "2024-02-15T12:34:56+00:00"}, indent=2),
        encoding="utf-8",
    )
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    # Populate the local firm dir.
    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)
    # Modified vs archive
    (fd / "tasks.md").write_text(
        "# Tasks policy\n\nDefault priority is medium.\n", encoding="utf-8"
    )
    (fd / "notes.md").write_text("# Notes policy\n", encoding="utf-8")
    # On disk but not in archive — surfaces as "removed".
    (fd / "events.md").write_text("# Events policy\n", encoding="utf-8")
    # contacts.md intentionally not on disk → surfaces as "added".

    result = runner.invoke(app, ["firm", "diff", str(archive)])

    # Changes detected → non-zero exit so callers can pipe-check.
    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined

    # Summary header lists every category.
    assert "contacts.md" in combined
    assert "tasks.md" in combined
    assert "notes.md" in combined
    assert "events.md" in combined

    # Buckets are labelled — the user needs to know which file is which.
    lower = combined.lower()
    assert "added" in lower
    assert "modified" in lower
    assert "removed" in lower

    # Per-file unified diff body is present (hunk header + file headers).
    assert "@@" in combined
    assert "--- " in combined
    assert "+++ " in combined

    # The modified body for tasks.md shows both the old (disk) line and the
    # new (archive) line — that's how unified diff carries the change.
    assert "-Default priority is medium." in combined
    assert "+Default priority is HIGH." in combined


def test_firm_diff_skips_meta_json_noise(runner, tmp_path: Path) -> None:
    """``_meta.json`` must not appear in the diff output even though
    ``pack`` strips it to the policy subset and the destination on disk
    carries generated keys (identity / cli_version / files). A bytewise
    diff would always show drift here — the diff command sidesteps that
    noise so the output reflects real policy drift only."""
    from wealthbox_tools.cli._skill_paths import firm_dir

    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)
    for name, body in bodies.items():
        (fd / name).write_text(body, encoding="utf-8")
    # Destination meta has the generated keys that pack strips.
    (fd / "_meta.json").write_text(
        json.dumps(
            {
                "identity": {"id": 1, "name": "Local Firm", "user_id": 1},
                "cli_version": "1.6.0",
                "files": {"categories.md": "2026-04-01T00:00:00+00:00"},
                "onboarded_at": "2024-02-15T12:34:56+00:00",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["firm", "diff", str(archive)])

    assert result.exit_code == 0, result.stdout
    combined = (result.stdout or "") + (result.stderr or "")
    assert "_meta.json" not in combined


def test_firm_diff_handles_missing_trailing_newline(tmp_path: Path) -> None:
    """When either side of a changed file lacks a trailing newline,
    ``difflib.unified_diff`` returns ``-``/``+`` records without
    terminators. The renderer must add a git-style
    ``\\ No newline at end of file`` marker so the output stays parseable
    as unified diff — otherwise lines glue together (``-old+new``) and
    can corrupt the next file header.
    """
    from wealthbox_tools.firm.diff import _unified

    rendered = _unified(b"old", b"new", a_label="contacts.md", b_label="contacts.md")
    # No "-old+new" concatenation.
    assert "-old+new" not in rendered
    # Both sides surface as separate records, each followed by the marker.
    assert "-old\n\\ No newline at end of file\n" in rendered
    assert "+new\n\\ No newline at end of file\n" in rendered
    # And every emitted line ends with a newline so a downstream consumer
    # (`splitlines`, a patch tool, etc.) parses it cleanly.
    for line in rendered.splitlines(keepends=True):
        assert line.endswith("\n"), repr(line)


def test_firm_diff_surfaces_clear_error_on_missing_archive(
    runner, tmp_path: Path
) -> None:
    """A missing archive path exits cleanly via BadParameter, not a stack trace —
    matches the ``import_firm`` error contract."""
    missing = tmp_path / "nope.zip"
    result = runner.invoke(app, ["firm", "diff", str(missing)])

    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined
