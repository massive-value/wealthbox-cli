"""Tests for ``wbox firm import`` and the underlying ``firm.archive`` unpack/apply.

Issue #36 — overwrite mode only. Sibling slices (#45 URL fetch, #46 merge /
abort-on-conflict, #47 diff, #48 post-import metadata) are blocked by this
one and will extend the same ``unpack`` / ``apply`` / ``ApplyMode`` surface.
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from wealthbox_tools.cli.main import app
from wealthbox_tools.firm.archive import (
    ApplyMode,
    ArchiveError,
    apply,
    pack,
    unpack,
)

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


_PINNED_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _populated_firm_dir(root: Path) -> dict[str, str]:
    """Create a firm dir matching the export-side fixture.

    Returns the hand-edited bodies so tests can assert round-trip equality.
    """
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


def _zip_with_manifest(path: Path, manifest: dict, bodies: dict[str, str] | None = None) -> Path:
    """Hand-craft a zip archive with the given manifest and optional file bodies."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(".manifest.json", json.dumps(manifest, indent=2) + "\n")
        for name, body in (bodies or {}).items():
            zf.writestr(name, body)
    path.write_bytes(buf.getvalue())
    return path


# --------------------------------------------------------------------------- #
# Round-trip: unpack + apply(overwrite)                                        #
# --------------------------------------------------------------------------- #


def test_round_trip_overwrite_writes_hand_edited_files(tmp_path: Path) -> None:
    """Pack → unpack → apply(overwrite) reproduces the hand-edited tree."""
    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    blob = pack(src, now=_PINNED_NOW)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(blob)

    plan = unpack(archive)
    dst = tmp_path / "dst"
    dst.mkdir()

    result = apply(plan, dst, ApplyMode.OVERWRITE)

    for name, expected in bodies.items():
        assert (dst / name).read_text(encoding="utf-8") == expected
    # Round-trip also restores the policy-shaped _meta.json.
    assert json.loads((dst / "_meta.json").read_text(encoding="utf-8")) == {
        "onboarded_at": "2024-02-15T12:34:56+00:00",
    }
    # ApplyResult reports every file actually written.
    assert set(result.written) == set(bodies) | {"_meta.json"}


def test_unpack_exposes_manifest(tmp_path: Path) -> None:
    """The plan carries the manifest so callers can introspect format_version etc."""
    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    plan = unpack(archive)

    assert plan.manifest["format_version"] == 1
    assert plan.manifest["exported_at"] == "2026-01-01T00:00:00+00:00"
    assert plan.manifest["source_firm_name"] is None  # no identity in the fixture


def test_apply_overwrite_replaces_existing_content(tmp_path: Path) -> None:
    """Overwrite truly overwrites — pre-existing content is replaced, not merged."""
    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "contacts.md").write_text("# stale local edits\n", encoding="utf-8")

    plan = unpack(archive)
    apply(plan, dst, ApplyMode.OVERWRITE)

    assert (dst / "contacts.md").read_text(encoding="utf-8") == bodies["contacts.md"]


def test_apply_overwrite_leaves_unrelated_files_alone(tmp_path: Path) -> None:
    """Generated files that weren't in the archive must not be touched.

    The archive is whitelist-only, so categories.md / custom-fields.md / users.md
    stay untouched on the destination side.
    """
    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "categories.md").write_text("# locally regenerated\n", encoding="utf-8")

    plan = unpack(archive)
    apply(plan, dst, ApplyMode.OVERWRITE)

    assert (dst / "categories.md").read_text(encoding="utf-8") == "# locally regenerated\n"


# --------------------------------------------------------------------------- #
# Manifest version validation                                                  #
# --------------------------------------------------------------------------- #


def test_unpack_rejects_unknown_format_version(tmp_path: Path) -> None:
    """A zip with format_version > 1 raises ArchiveError with a clear message."""
    archive = _zip_with_manifest(
        tmp_path / "future.zip",
        manifest={
            "format_version": 99,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "source_firm_name": None,
            "source_cli_version": "9.9.9",
        },
        bodies={"contacts.md": "# from the future\n"},
    )

    with pytest.raises(ArchiveError) as excinfo:
        unpack(archive)

    msg = str(excinfo.value)
    assert "format_version" in msg
    assert "99" in msg


def test_apply_mode_enum_has_three_values() -> None:
    """The enum carries the three modes named in the brief, even though only
    overwrite is implemented in this slice — sibling issues #46/#47 wire the
    others up against the same surface."""
    assert ApplyMode("overwrite") is ApplyMode.OVERWRITE
    assert ApplyMode("merge") is ApplyMode.MERGE
    assert ApplyMode("abort-on-conflict") is ApplyMode.ABORT_ON_CONFLICT


# --------------------------------------------------------------------------- #
# CLI: wbox firm import <path>                                                 #
# --------------------------------------------------------------------------- #


def test_firm_import_cli_yes_skips_prompt_and_writes(runner, tmp_path: Path) -> None:
    """`wbox firm import <path> --yes` overwrites the local firm dir without prompting."""
    from wealthbox_tools.cli._skill_paths import firm_dir

    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["firm", "import", str(archive), "--yes"])

    assert result.exit_code == 0, result.stdout
    for name, expected in bodies.items():
        assert (fd / name).read_text(encoding="utf-8") == expected


def test_firm_import_cli_aborts_when_user_declines_prompt(
    runner, tmp_path: Path
) -> None:
    """Without ``--yes``, declining the prompt leaves the firm dir untouched."""
    from wealthbox_tools.cli._skill_paths import firm_dir

    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)
    pre_existing = "# DO NOT TOUCH\n"
    (fd / "contacts.md").write_text(pre_existing, encoding="utf-8")

    result = runner.invoke(app, ["firm", "import", str(archive)], input="n\n")

    assert result.exit_code != 0
    assert (fd / "contacts.md").read_text(encoding="utf-8") == pre_existing


def test_firm_import_cli_surfaces_clear_error_on_bad_format_version(
    runner, tmp_path: Path
) -> None:
    """ArchiveError must reach the user as a clean message, not a stack trace."""
    archive = _zip_with_manifest(
        tmp_path / "future.zip",
        manifest={
            "format_version": 99,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "source_firm_name": None,
            "source_cli_version": "9.9.9",
        },
    )

    result = runner.invoke(app, ["firm", "import", str(archive), "--yes"])

    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "format_version" in combined
    assert "Traceback" not in combined
