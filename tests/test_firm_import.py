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


def test_apply_overwrite_merges_meta_instead_of_replacing(tmp_path: Path) -> None:
    """``_meta.json`` is the only archive entry that needs merge semantics.

    ``pack`` deliberately strips ``_meta.json`` down to the policy subset
    (just ``onboarded_at``). If ``apply`` wrote that subset wholesale, it
    would destroy the destination's ``identity``, ``cli_version``, and
    ``files`` timestamps that ``wbox doctor`` and the skill bootstrap
    machinery depend on. Apply must merge the policy keys *into* the
    existing meta, not replace it.
    """
    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    pre_existing = {
        "identity": {"id": 42, "name": "Local Firm", "user_id": 7},
        "cli_version": "1.6.0",
        "files": {"categories.md": "2026-04-01T00:00:00+00:00"},
        "onboarded_at": "2025-01-01T00:00:00+00:00",
    }
    (dst / "_meta.json").write_text(json.dumps(pre_existing, indent=2), encoding="utf-8")

    plan = unpack(archive)
    apply(plan, dst, ApplyMode.OVERWRITE)

    merged = json.loads((dst / "_meta.json").read_text(encoding="utf-8"))
    # Policy keys from the archive overwrite the destination's values.
    assert merged["onboarded_at"] == "2024-02-15T12:34:56+00:00"
    # Generated/identity keys survive.
    assert merged["identity"] == {"id": 42, "name": "Local Firm", "user_id": 7}
    assert merged["cli_version"] == "1.6.0"
    assert merged["files"] == {"categories.md": "2026-04-01T00:00:00+00:00"}


def test_apply_filters_incoming_meta_to_policy_keys(tmp_path: Path) -> None:
    """A tampered ``_meta.json`` that includes generated keys (identity,
    cli_version, files) must NOT overwrite the destination's values for
    those keys. ``pack`` only writes META_POLICY_KEYS into the archive's
    meta, so ``apply`` must symmetrically only accept those keys —
    otherwise the whitelist-symmetry from #36's fix only applies at
    file-name granularity, not at the key-level granularity that pack
    enforces inside ``_meta.json``.
    """
    # Hand-craft a tampered archive whose _meta.json contains a forged
    # identity. The whitelist-only file check passes (it's _meta.json), so
    # the protection has to live in the merge step.
    tampered_meta = {
        "onboarded_at": "2024-02-15T12:34:56+00:00",  # legit policy key
        "identity": {"id": 999, "name": "Forged", "user_id": 999},
        "cli_version": "9.9.9",
        "files": {"categories.md": "1970-01-01T00:00:00+00:00"},
    }
    archive = _zip_with_manifest(
        tmp_path / "tampered.zip",
        manifest={
            "format_version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "source_firm_name": None,
            "source_cli_version": "1.0.0",
        },
        bodies={"_meta.json": json.dumps(tampered_meta, indent=2)},
    )

    dst = tmp_path / "dst"
    dst.mkdir()
    legitimate = {
        "identity": {"id": 42, "name": "Local Firm", "user_id": 7},
        "cli_version": "1.6.0",
        "files": {"categories.md": "2026-04-01T00:00:00+00:00"},
        "onboarded_at": "2025-01-01T00:00:00+00:00",
    }
    (dst / "_meta.json").write_text(json.dumps(legitimate, indent=2), encoding="utf-8")

    plan = unpack(archive)
    apply(plan, dst, ApplyMode.OVERWRITE)

    merged = json.loads((dst / "_meta.json").read_text(encoding="utf-8"))
    # Policy key is taken from the archive.
    assert merged["onboarded_at"] == "2024-02-15T12:34:56+00:00"
    # Generated keys must NOT have been overwritten by the tampered archive.
    assert merged["identity"] == legitimate["identity"]
    assert merged["cli_version"] == legitimate["cli_version"]
    assert merged["files"] == legitimate["files"]


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


def test_unpack_wraps_missing_file_as_archive_error(tmp_path: Path) -> None:
    """A non-existent path raises ArchiveError, not FileNotFoundError, so the
    CLI's ``except ArchiveError`` branch is reached and the user sees a clean
    BadParameter rather than a stack trace."""
    missing = tmp_path / "does_not_exist.zip"
    with pytest.raises(ArchiveError) as excinfo:
        unpack(missing)
    assert "does_not_exist.zip" in str(excinfo.value)


@pytest.mark.parametrize(
    "evil_name",
    [
        "../escape.md",                # parent traversal
        "subdir/../../escape.md",      # nested traversal
        "/abs/path.md",                # posix absolute
        "C:/Windows/system.md",        # windows drive letter
        "..\\escape.md",               # backslash traversal (zip spec is /, but
                                       # malicious archives may use \\ to bypass
                                       # naive checks on Windows)
        ".",                           # current-dir; would resolve onto firm_dir
        "./contacts.md",               # leading-dot segment
        "contacts/./policy.md",        # mid-path-dot segment
        "subdir/",                     # directory entry; write_bytes on a dir
                                       # raises IsADirectoryError otherwise
        "foo//bar.md",                 # empty middle segment
    ],
)
def test_unpack_rejects_unsafe_archive_entry_paths(
    tmp_path: Path, evil_name: str
) -> None:
    """Path-traversal and absolute entries must not survive unpack.

    Without this guard, ``apply`` would write outside ``firm_dir`` — once #45
    lets URLs be the source, an attacker-crafted archive could overwrite any
    file the user can write."""
    archive = _zip_with_manifest(
        tmp_path / "evil.zip",
        manifest={
            "format_version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "source_firm_name": None,
            "source_cli_version": "1.0.0",
        },
        bodies={evil_name: "# pwned\n"},
    )
    with pytest.raises(ArchiveError) as excinfo:
        unpack(archive)
    assert "unsafe" in str(excinfo.value).lower() or "path" in str(excinfo.value).lower()


@pytest.mark.parametrize(
    "stray_name",
    [
        "categories.md",        # generated; would poison the local cache
        "custom-fields.md",     # generated
        "users.md",             # generated
        "subdir/policy.md",     # nested anything
        "firm.zip",             # arbitrary
    ],
)
def test_unpack_rejects_non_policy_entries(tmp_path: Path, stray_name: str) -> None:
    """``pack`` is whitelist-only (HAND_EDITED_FILES + _meta.json); ``unpack``
    must enforce the same whitelist so a tampered archive can't smuggle
    generated files (``categories.md``, ``users.md``) past apply and poison
    caches that the skill bootstrap relies on."""
    archive = _zip_with_manifest(
        tmp_path / "tampered.zip",
        manifest={
            "format_version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "source_firm_name": None,
            "source_cli_version": "1.0.0",
        },
        bodies={
            "contacts.md": "# Contacts policy\n",
            stray_name: "# tampered payload\n",
        },
    )
    with pytest.raises(ArchiveError) as excinfo:
        unpack(archive)
    assert stray_name in str(excinfo.value)


def test_apply_rejects_unsafe_paths_in_hand_built_plan(tmp_path: Path) -> None:
    """Defense in depth: ImportPlan is a public dataclass, so apply also guards.

    If a caller constructs a plan whose ``files`` dict contains an unsafe
    name (bypassing ``unpack``), ``apply`` must refuse to write outside
    ``firm_dir`` rather than trust the plan blindly.
    """
    from wealthbox_tools.firm.archive import ImportPlan

    dst = tmp_path / "firm"
    dst.mkdir()
    plan = ImportPlan(
        manifest={"format_version": 1},
        files={"../escape.md": b"# pwned\n"},
    )
    with pytest.raises(ArchiveError):
        apply(plan, dst, ApplyMode.OVERWRITE)
    assert not (tmp_path / "escape.md").exists()


def test_firm_import_cli_surfaces_clear_error_on_missing_file(
    runner, tmp_path: Path
) -> None:
    """A missing archive path must exit cleanly via BadParameter, not crash."""
    missing = tmp_path / "nope.zip"

    result = runner.invoke(app, ["firm", "import", str(missing), "--yes"])

    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined


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
