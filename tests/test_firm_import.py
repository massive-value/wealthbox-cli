"""Tests for ``wbox firm import`` and the underlying ``firm.archive`` unpack/apply.

Covers all three :class:`ApplyMode` values — ``overwrite`` (#36), and
``merge`` / ``abort-on-conflict`` (#46) — against the same ``unpack`` /
``apply`` / CLI surface. Sibling slices (#45 URL fetch, #47 diff, #48
post-import metadata) extend the same surface separately.
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
import respx

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


@pytest.mark.parametrize(
    "bad_meta_body",
    [
        "not json at all",                # JSONDecodeError
        "[1, 2, 3]",                      # JSON array, not object
        '"a string"',                     # JSON string, not object
        "null",                           # JSON null
    ],
)
def test_unpack_rejects_malformed_meta_json(tmp_path: Path, bad_meta_body: str) -> None:
    """A tampered ``_meta.json`` with invalid JSON or a non-object payload
    must be rejected at unpack time. The previous fallback wrote the raw
    bytes verbatim, which bypassed META_POLICY_KEYS filtering and could
    corrupt the destination's identity/cli_version/files cache."""
    archive = _zip_with_manifest(
        tmp_path / "evil.zip",
        manifest={
            "format_version": 1,
            "exported_at": "2026-01-01T00:00:00+00:00",
            "source_firm_name": None,
            "source_cli_version": "1.0.0",
        },
        bodies={"_meta.json": bad_meta_body},
    )
    with pytest.raises(ArchiveError) as excinfo:
        unpack(archive)
    assert "_meta.json" in str(excinfo.value)


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
    """The enum carries the three modes named in the brief: overwrite,
    merge, and abort-on-conflict. All three are implemented and exposed
    through the same :func:`apply` surface."""
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


# --------------------------------------------------------------------------- #
# Post-import provenance (#48)                                                #
# --------------------------------------------------------------------------- #


def test_apply_writes_last_imported_provenance(tmp_path: Path) -> None:
    """A successful ``apply`` stamps ``last_imported_from`` /
    ``last_imported_at`` into the destination's ``_meta.json`` so the
    doctor can warn when the data goes stale (#48)."""
    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    plan = unpack(archive)

    pinned = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    apply(plan, dst, ApplyMode.OVERWRITE, source=str(archive), now=pinned)

    meta = json.loads((dst / "_meta.json").read_text(encoding="utf-8"))
    assert meta["last_imported_from"] == str(archive)
    assert meta["last_imported_at"] == pinned.isoformat()
    # Policy keys carried in the archive still merge through.
    assert meta["onboarded_at"] == "2024-02-15T12:34:56+00:00"


def test_apply_provenance_preserves_existing_generated_keys(tmp_path: Path) -> None:
    """Provenance stamping must not clobber identity / cli_version / files
    on the destination — those are generated keys that ``wbox doctor`` and
    the bootstrap machinery rely on."""
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
    pinned = datetime(2026, 5, 9, 12, 0, 0, tzinfo=timezone.utc)
    apply(plan, dst, ApplyMode.OVERWRITE, source="https://firm.example/export.zip", now=pinned)

    meta = json.loads((dst / "_meta.json").read_text(encoding="utf-8"))
    assert meta["identity"] == pre_existing["identity"]
    assert meta["cli_version"] == pre_existing["cli_version"]
    assert meta["files"] == pre_existing["files"]
    assert meta["last_imported_from"] == "https://firm.example/export.zip"
    assert meta["last_imported_at"] == pinned.isoformat()


def test_apply_without_source_does_not_write_provenance(tmp_path: Path) -> None:
    """Library callers that omit ``source`` (e.g. internal tests) get the
    pre-#48 behavior — no provenance is stamped."""
    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    plan = unpack(archive)
    apply(plan, dst, ApplyMode.OVERWRITE)  # no source kwarg

    meta = json.loads((dst / "_meta.json").read_text(encoding="utf-8"))
    assert "last_imported_from" not in meta
    assert "last_imported_at" not in meta


# --------------------------------------------------------------------------- #
# Apply: merge mode                                                            #
# --------------------------------------------------------------------------- #


def test_apply_merge_skips_existing_files_and_writes_new_ones(tmp_path: Path) -> None:
    """``MERGE`` writes only files that don't already exist locally.

    The destination has its own ``contacts.md`` and ``tasks.md`` — those
    should be left untouched. The remaining hand-edited files in the plan
    don't exist locally yet, so they should land verbatim.
    """
    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    local_contacts = "# locally curated contacts policy\n"
    local_tasks = "# locally curated tasks policy\n"
    (dst / "contacts.md").write_text(local_contacts, encoding="utf-8")
    (dst / "tasks.md").write_text(local_tasks, encoding="utf-8")

    plan = unpack(archive)
    result = apply(plan, dst, ApplyMode.MERGE)

    # Pre-existing local files are preserved.
    assert (dst / "contacts.md").read_text(encoding="utf-8") == local_contacts
    assert (dst / "tasks.md").read_text(encoding="utf-8") == local_tasks
    # Files that didn't exist locally land from the archive.
    for name in ("notes.md", "events.md", "opportunities.md", "projects.md", "workflows.md"):
        assert (dst / name).read_text(encoding="utf-8") == bodies[name]
    # ApplyResult only reports files actually written. _meta.json always
    # merges (key-level), so it should appear in `written`; the two skipped
    # markdown files should not.
    assert "contacts.md" not in result.written
    assert "tasks.md" not in result.written
    assert "notes.md" in result.written
    assert "_meta.json" in result.written


def test_apply_merge_meta_still_merges_policy_keys(tmp_path: Path) -> None:
    """``_meta.json`` is the one entry that key-merges in every mode.

    ``pack`` strips ``_meta.json`` to just the policy subset
    (``onboarded_at``); skipping it whole in MERGE would mean a firm that
    re-imports an updated policy never picks up new policy keys, even
    though no destination data is being clobbered. The key-level merge
    (policy keys overwritten, generated keys preserved) is the right
    behavior in MERGE mode too.
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
    apply(plan, dst, ApplyMode.MERGE)

    merged = json.loads((dst / "_meta.json").read_text(encoding="utf-8"))
    # Policy key from the archive lands.
    assert merged["onboarded_at"] == "2024-02-15T12:34:56+00:00"
    # Generated keys survive.
    assert merged["identity"] == pre_existing["identity"]
    assert merged["cli_version"] == pre_existing["cli_version"]
    assert merged["files"] == pre_existing["files"]


# --------------------------------------------------------------------------- #
# Apply: abort-on-conflict mode                                                #
# --------------------------------------------------------------------------- #


def test_apply_abort_on_conflict_raises_and_writes_nothing(tmp_path: Path) -> None:
    """``ABORT_ON_CONFLICT`` refuses to write anything if any file would be
    replaced. The whole import is aborted — no partial state, no files
    written, no provenance stamped. ``_meta.json`` is excluded from the
    conflict check (it always key-merges), so its presence on disk does
    not on its own trigger an abort.
    """
    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    # One pre-existing local hand-edited file should be enough to abort.
    local_contacts = "# locally curated contacts policy\n"
    (dst / "contacts.md").write_text(local_contacts, encoding="utf-8")

    plan = unpack(archive)
    with pytest.raises(ArchiveError) as excinfo:
        apply(plan, dst, ApplyMode.ABORT_ON_CONFLICT)
    assert "contacts.md" in str(excinfo.value)

    # The conflicting file must be untouched.
    assert (dst / "contacts.md").read_text(encoding="utf-8") == local_contacts
    # No other plan files should have been written either — the abort is
    # all-or-nothing.
    for name in ("tasks.md", "notes.md", "events.md", "opportunities.md", "projects.md", "workflows.md"):
        assert not (dst / name).exists()
    # And no _meta.json should have been written, since the operation
    # aborted before any write happened.
    assert not (dst / "_meta.json").exists()


def test_apply_abort_on_conflict_writes_when_no_conflicts(tmp_path: Path) -> None:
    """When no plan file would replace a local file, ABORT_ON_CONFLICT writes
    every file in the plan — same shape as OVERWRITE on a clean tree."""
    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()

    plan = unpack(archive)
    result = apply(plan, dst, ApplyMode.ABORT_ON_CONFLICT)

    for name, expected in bodies.items():
        assert (dst / name).read_text(encoding="utf-8") == expected
    assert set(result.written) == set(bodies) | {"_meta.json"}


# --------------------------------------------------------------------------- #
# CLI: provenance + mode tests                                                 #
# --------------------------------------------------------------------------- #


def test_firm_import_cli_stamps_provenance(runner, tmp_path: Path) -> None:
    """The CLI passes the archive path through to ``apply`` so the user's
    firm dir picks up the freshness fields after a real ``wbox firm import``."""
    from wealthbox_tools.cli._skill_paths import firm_meta_path

    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    result = runner.invoke(app, ["firm", "import", str(archive), "--yes"])
    assert result.exit_code == 0, result.stdout

    meta = json.loads(firm_meta_path().read_text(encoding="utf-8"))
    assert meta["last_imported_from"] == str(archive)
    assert isinstance(meta.get("last_imported_at"), str) and meta["last_imported_at"]


def test_firm_import_cli_merge_mode_skips_existing_files(
    runner, tmp_path: Path
) -> None:
    """`wbox firm import <path> --mode merge --yes` skips files that exist locally."""
    from wealthbox_tools.cli._skill_paths import firm_dir

    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)
    local_contacts = "# locally curated\n"
    (fd / "contacts.md").write_text(local_contacts, encoding="utf-8")

    result = runner.invoke(
        app, ["firm", "import", str(archive), "--mode", "merge", "--yes"]
    )

    assert result.exit_code == 0, result.stdout
    # Existing file preserved.
    assert (fd / "contacts.md").read_text(encoding="utf-8") == local_contacts
    # Newly-written file lands.
    assert (fd / "notes.md").read_text(encoding="utf-8") == bodies["notes.md"]


def test_firm_import_cli_abort_on_conflict_mode_aborts_cleanly(
    runner, tmp_path: Path
) -> None:
    """`wbox firm import <path> --mode abort-on-conflict --yes` exits non-zero
    when any local file would be replaced, and writes nothing."""
    from wealthbox_tools.cli._skill_paths import firm_dir

    src = tmp_path / "src"
    _populated_firm_dir(src)
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)
    local_contacts = "# locally curated\n"
    (fd / "contacts.md").write_text(local_contacts, encoding="utf-8")

    result = runner.invoke(
        app,
        ["firm", "import", str(archive), "--mode", "abort-on-conflict", "--yes"],
    )

    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined
    # Conflicting file untouched.
    assert (fd / "contacts.md").read_text(encoding="utf-8") == local_contacts
    # And the non-conflicting files were not written either.
    for name in ("tasks.md", "notes.md", "events.md", "opportunities.md", "projects.md", "workflows.md"):
        assert not (fd / name).exists()


# --------------------------------------------------------------------------- #
# URL fetch (#45)                                                             #
# --------------------------------------------------------------------------- #


@respx.mock
def test_unpack_fetches_url_with_single_get(tmp_path: Path) -> None:
    """``unpack("https://...")`` performs a single GET and operates on the
    returned bytes identically to the local-path code path.

    The URL branch is byte-for-byte equivalent to passing the same archive
    as a local file: same manifest, same hand-edited bodies, same plan.
    """
    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    blob = pack(src, now=_PINNED_NOW)

    url = "https://example.com/firm.zip"
    route = respx.get(url).mock(
        return_value=httpx.Response(200, content=blob)
    )

    plan = unpack(url)

    # Exactly one GET, no retries, no probes.
    assert route.call_count == 1
    # Manifest and files match the local-path round trip.
    assert plan.manifest["format_version"] == 1
    assert plan.manifest["exported_at"] == "2026-01-01T00:00:00+00:00"
    for name, expected in bodies.items():
        assert plan.files[name].decode("utf-8") == expected


@respx.mock
def test_unpack_url_then_apply_round_trip(tmp_path: Path) -> None:
    """End-to-end via URL: unpack from URL, then apply to a fresh firm dir
    and assert every hand-edited body lands. Confirms the URL bytes path
    feeds the same downstream apply machinery as the local-path branch."""
    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    blob = pack(src, now=_PINNED_NOW)

    url = "https://example.com/firm.zip"
    respx.get(url).mock(return_value=httpx.Response(200, content=blob))

    plan = unpack(url)

    dst = tmp_path / "dst"
    dst.mkdir()
    apply(plan, dst, ApplyMode.OVERWRITE)

    for name, expected in bodies.items():
        assert (dst / name).read_text(encoding="utf-8") == expected


@respx.mock
def test_unpack_url_non_2xx_raises_archive_error() -> None:
    """A non-2xx HTTP response surfaces as :class:`ArchiveError` with a
    clean message — the CLI's ``except ArchiveError`` branch must reach
    the user without a stack trace."""
    url = "https://example.com/firm.zip"
    respx.get(url).mock(return_value=httpx.Response(404, text="not found"))

    with pytest.raises(ArchiveError) as excinfo:
        unpack(url)

    msg = str(excinfo.value)
    assert "404" in msg
    assert url in msg


@respx.mock
def test_unpack_url_network_error_raises_archive_error() -> None:
    """A transport-level failure (DNS, connection refused, etc.) is wrapped
    as ArchiveError so the CLI surfaces it cleanly."""
    url = "https://example.com/firm.zip"
    respx.get(url).mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(ArchiveError) as excinfo:
        unpack(url)

    assert url in str(excinfo.value)


@respx.mock
def test_firm_import_cli_accepts_url(runner, tmp_path: Path) -> None:
    """`wbox firm import <url> --yes` fetches the archive and writes the
    firm directory just like the local-path form."""
    from wealthbox_tools.cli._skill_paths import firm_dir

    src = tmp_path / "src"
    bodies = _populated_firm_dir(src)
    blob = pack(src, now=_PINNED_NOW)

    url = "https://example.com/firm.zip"
    respx.get(url).mock(return_value=httpx.Response(200, content=blob))

    fd = firm_dir()
    fd.mkdir(parents=True, exist_ok=True)

    result = runner.invoke(app, ["firm", "import", url, "--yes"])

    assert result.exit_code == 0, (result.stdout or "") + (result.stderr or "")
    for name, expected in bodies.items():
        assert (fd / name).read_text(encoding="utf-8") == expected


@respx.mock
def test_firm_import_cli_url_non_2xx_surfaces_clean_error(
    runner, tmp_path: Path
) -> None:
    """A non-2xx URL fetch shows the user a clean error, not a stack trace."""
    url = "https://example.com/missing.zip"
    respx.get(url).mock(return_value=httpx.Response(503, text="boom"))

    result = runner.invoke(app, ["firm", "import", url, "--yes"])

    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Traceback" not in combined
    assert "503" in combined


# --------------------------------------------------------------------------- #
# Bootstrap Q&A skip on imported `onboarded_at` (#49)                          #
# --------------------------------------------------------------------------- #


def test_apply_propagates_onboarded_at_from_imported_meta(tmp_path: Path) -> None:
    """A source firm whose ``_meta.json`` has ``onboarded_at`` set must seed
    the destination's ``onboarded_at`` after a successful import.

    This is the gate the agent-side bootstrap Q&A keys off — once a peer
    machine has captured the qualitative firm policy and exported, importing
    that archive on a fresh install should mark the firm onboarded here too,
    so the bootstrap.md Q&A path is skipped automatically.
    """
    src = tmp_path / "src"
    _populated_firm_dir(src)  # writes onboarded_at = "2024-02-15T12:34:56+00:00"
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    dst = tmp_path / "dst"
    dst.mkdir()
    # Destination has no _meta.json at all — the fresh-install case.
    plan = unpack(archive)
    apply(plan, dst, ApplyMode.OVERWRITE)

    meta = json.loads((dst / "_meta.json").read_text(encoding="utf-8"))
    assert meta["onboarded_at"] == "2024-02-15T12:34:56+00:00"


def test_apply_does_not_set_onboarded_at_when_source_lacks_it(
    tmp_path: Path,
) -> None:
    """When the source firm has not been onboarded (no ``onboarded_at`` in its
    ``_meta.json``), apply must NOT invent a value — the destination's
    ``onboarded_at`` field is unchanged.

    A pre-existing local ``onboarded_at`` survives (provenance write merges
    on top of it); a missing local key stays missing. The agent-side Q&A
    path then runs as normal because the gate in bootstrap.md is still tripped.
    """
    src = tmp_path / "src"
    src.mkdir()
    # Hand-edited policy is present but no _meta.json with onboarded_at.
    (src / "contacts.md").write_text("# Contacts policy\n", encoding="utf-8")
    archive = tmp_path / "firm.zip"
    archive.write_bytes(pack(src, now=_PINNED_NOW))

    # Case 1: destination has a pre-existing `onboarded_at` locally — it
    # must survive the import unchanged.
    dst_with = tmp_path / "dst_with"
    dst_with.mkdir()
    pre_existing = {"onboarded_at": "2025-01-01T00:00:00+00:00"}
    (dst_with / "_meta.json").write_text(
        json.dumps(pre_existing, indent=2), encoding="utf-8"
    )

    plan = unpack(archive)
    apply(plan, dst_with, ApplyMode.OVERWRITE)

    meta_with = json.loads((dst_with / "_meta.json").read_text(encoding="utf-8"))
    assert meta_with["onboarded_at"] == "2025-01-01T00:00:00+00:00"

    # Case 2: destination has no _meta.json — the field must remain absent
    # after a real CLI-shaped import (provenance write may create the file,
    # but `onboarded_at` is never invented from thin air).
    dst_without = tmp_path / "dst_without"
    dst_without.mkdir()

    plan = unpack(archive)
    # Pass `source` so the post-import provenance write happens (mirrors
    # the CLI surface in src/wealthbox_tools/cli/firm.py, which always
    # forwards the archive path). Otherwise no `_meta.json` is written at
    # all and there's no field to assert against.
    apply(plan, dst_without, ApplyMode.OVERWRITE, source=str(archive))

    meta_without = json.loads(
        (dst_without / "_meta.json").read_text(encoding="utf-8")
    )
    assert "onboarded_at" not in meta_without


def test_bootstrap_md_skips_when_onboarded_at_is_set() -> None:
    """The skill template ``bootstrap.md`` must instruct the agent to
    short-circuit when ``onboarded_at`` is already set — that's the
    fresh-install-then-import flow where another machine ran the Q&A and
    the result was synced here via ``wbox firm import``.

    The template ships inside the package; reading it from importlib
    resources keeps the assertion working whether tests run from a wheel
    install or an editable checkout.
    """
    from importlib.resources import files

    bootstrap_text = (
        files("wealthbox_tools")
        .joinpath("skills/wealthbox-crm/bootstrap.md")
        .read_text(encoding="utf-8")
    )
    # The early-out check must reference the gate field by name and tell
    # the agent to skip when it's already populated.
    assert "onboarded_at" in bootstrap_text
    lower = bootstrap_text.lower()
    assert "already onboarded" in lower
    assert "skip" in lower
