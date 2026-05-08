"""Tests for the skill-reference markdown auto-generator.

The generator at :mod:`wealthbox_tools.internals.skill_ref_gen` rewrites
the content between ``<!-- auto-gen:flags -->`` markers in skill reference
markdown files. Slice #30 covers the ``contacts`` resource only; later
slices roll markers across the rest of references/.

These tests run the generator against an isolated copy of the references
tree so they neither depend on nor mutate the real markdown files.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from wealthbox_tools.internals import skill_ref_gen
from wealthbox_tools.internals.skill_ref_gen import (
    CLOSE_MARKER,
    OPEN_MARKER,
    regenerate_all,
)

# The single file in scope for slice #30. Other reference files are
# handled in subsequent issues (#35).
_RESOURCE = "contacts"
_FILENAME = "contacts.md"


def _real_references_dir() -> Path:
    """Return the in-tree references directory the generator targets by default."""
    return (
        Path(skill_ref_gen.__file__).resolve().parent.parent
        / "skills"
        / "wealthbox-crm"
        / "references"
    )


@pytest.fixture
def refs_dir(tmp_path: Path) -> Path:
    """Copy the real references dir to a tmp dir for isolated mutation."""
    src = _real_references_dir()
    dst = tmp_path / "references"
    shutil.copytree(src, dst)
    return dst


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Idempotence
# ---------------------------------------------------------------------------

def test_idempotent_against_freshly_regenerated_tree(refs_dir: Path) -> None:
    """Two consecutive regens of an isolated tree must produce zero changes
    on the second pass."""
    first = regenerate_all(references_dir=refs_dir)
    # The first pass should populate the markers (initial commit ships with
    # empty markers); after that, a re-run is a no-op.
    second = regenerate_all(references_dir=refs_dir)
    assert second.modified == [], (
        f"second regen unexpectedly modified files: {second.modified}\n"
        f"first pass modified: {first.modified}"
    )


# ---------------------------------------------------------------------------
# 2. Drift detection
# ---------------------------------------------------------------------------

def test_drift_detection_restores_real_flags(refs_dir: Path) -> None:
    """If a hand-edit injects a fake flag inside the markers, the next
    regen removes the fake and restores the real flags."""
    target = refs_dir / _FILENAME
    # Bring the file into a freshly-generated state first.
    regenerate_all(references_dir=refs_dir)
    baseline = _read(target)

    # Introduce drift: insert a fake flag row inside the auto-gen block.
    fake = "FAKE-FLAG-SHOULD-BE-REMOVED"
    drifted = baseline.replace(
        OPEN_MARKER,
        OPEN_MARKER + f"\n| `--{fake}` | TEXT | - | bogus |",
        1,
    )
    assert fake in drifted
    _write(target, drifted)

    result = regenerate_all(references_dir=refs_dir)
    assert target in result.modified
    after = _read(target)
    assert fake not in after
    # And the real flags from the contacts list command should appear.
    assert "--first-name" in after
    assert "--contact-type" in after


# ---------------------------------------------------------------------------
# 3. Editorial preservation
# ---------------------------------------------------------------------------

def test_editorial_content_outside_markers_is_preserved(refs_dir: Path) -> None:
    """Hand-edits outside the auto-gen markers must not be touched by
    subsequent regens, even when the generated block is rewritten."""
    target = refs_dir / _FILENAME
    # Regenerate once to settle the auto-gen block.
    regenerate_all(references_dir=refs_dir)

    # Add a Tips section after the closing marker.
    tip = "## Tips\n\nDon't forget to bring a towel.\n"
    content = _read(target)
    edited = content.replace(CLOSE_MARKER, CLOSE_MARKER + "\n\n" + tip, 1)
    _write(target, edited)

    # Force a regen by introducing drift inside the markers — this proves
    # that even when the generator rewrites the block, the editorial
    # section is left intact.
    drifted = edited.replace(
        OPEN_MARKER,
        OPEN_MARKER + "\n<!-- forcibly-drifted -->",
        1,
    )
    _write(target, drifted)

    regenerate_all(references_dir=refs_dir)
    after = _read(target)
    assert tip.strip() in after
    assert "forcibly-drifted" not in after


# ---------------------------------------------------------------------------
# 4. Missing markers
# ---------------------------------------------------------------------------

def test_missing_markers_skips_file_with_warning(
    refs_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A markdown file with no auto-gen markers is left unchanged and a
    warning is emitted to stderr."""
    target = refs_dir / _FILENAME
    no_markers = "# Contacts\n\nNo markers here. Hand-written only.\n"
    _write(target, no_markers)

    result = regenerate_all(references_dir=refs_dir)
    captured = capsys.readouterr()

    assert _read(target) == no_markers
    assert target in result.skipped_no_markers
    assert target not in result.modified
    assert "auto-gen markers not found" in captured.err
    assert str(target) in captured.err


# ---------------------------------------------------------------------------
# 5. Determinism
# ---------------------------------------------------------------------------

def test_byte_for_byte_deterministic(tmp_path: Path) -> None:
    """Two independent regens against identical fresh inputs produce
    byte-identical files."""
    src = _real_references_dir()

    a = tmp_path / "a"
    b = tmp_path / "b"
    shutil.copytree(src, a)
    shutil.copytree(src, b)

    regenerate_all(references_dir=a)
    regenerate_all(references_dir=b)

    bytes_a = (a / _FILENAME).read_bytes()
    bytes_b = (b / _FILENAME).read_bytes()
    assert bytes_a == bytes_b


# ---------------------------------------------------------------------------
# 6. Enum rendering
# ---------------------------------------------------------------------------

def test_enum_field_renders_bulleted_choice_list(refs_dir: Path) -> None:
    """A Pydantic/Typer enum-typed flag (e.g. `--type` on `contacts list`,
    bound to ``RecordType``) must render as a bulleted list of valid values
    in the generated block."""
    target = refs_dir / _FILENAME
    regenerate_all(references_dir=refs_dir)
    content = _read(target)

    # `wbox contacts list --type` is bound to RecordType — Person,
    # Household, Organization, Trust.
    # Find the generated block and assert structure.
    assert OPEN_MARKER in content and CLOSE_MARKER in content
    block = content.split(OPEN_MARKER, 1)[1].split(CLOSE_MARKER, 1)[0]
    assert "**Choices for `--type`:**" in block
    for value in ("Person", "Household", "Organization", "Trust"):
        assert f"- `{value}`" in block


# ---------------------------------------------------------------------------
# Hidden-CLI smoke test (acceptance criterion: command is wired)
# ---------------------------------------------------------------------------

def test_internals_subapp_hidden_from_help() -> None:
    """`internals` must not surface in `wbox --help` output."""
    from typer.testing import CliRunner

    from wealthbox_tools.cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.stdout
    assert "internals" not in result.stdout


def test_internals_regen_skill_refs_runs(refs_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`wbox internals regen-skill-refs` invokes the generator end-to-end."""
    # Redirect the generator at our isolated tmp tree so the test never
    # mutates the real in-tree markdown.
    from typer.testing import CliRunner

    from wealthbox_tools.cli.main import app

    monkeypatch.setattr(
        skill_ref_gen, "_references_dir", lambda: refs_dir
    )

    runner = CliRunner()
    result = runner.invoke(app, ["internals", "regen-skill-refs"])
    assert result.exit_code == 0, result.stdout + "\n--stderr--\n" + (result.stderr or "")


# ---------------------------------------------------------------------------
# Map-typo guard — a stale RESOURCE_REFERENCE_MAP entry must fail loudly,
# not silently overwrite a reference file with an empty flag block.
# ---------------------------------------------------------------------------

def test_unknown_mapped_resource_raises(
    refs_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If RESOURCE_REFERENCE_MAP names a resource that is not registered on the
    root Typer app (typo, rename, or removed sub-app), regenerate_all must
    raise rather than rewrite the target file with empty content."""
    # Seed a markdown file with markers around real content so we can verify
    # it is not mutated when the generator raises.
    bogus_md = refs_dir / "no-such-resource.md"
    bogus_md.write_text(
        f"{OPEN_MARKER}\nplaceholder content that must survive\n{CLOSE_MARKER}\n",
        encoding="utf-8",
    )
    before = bogus_md.read_text(encoding="utf-8")

    monkeypatch.setattr(
        skill_ref_gen,
        "RESOURCE_REFERENCE_MAP",
        {"no-such-resource": "no-such-resource.md"},
    )

    with pytest.raises(KeyError, match="no-such-resource"):
        regenerate_all(references_dir=refs_dir)

    # File untouched.
    assert bogus_md.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# Self-check — guarantee the suite was actually pulled into pytest
# ---------------------------------------------------------------------------

def test_module_under_test_is_importable() -> None:
    assert "wealthbox_tools.internals.skill_ref_gen" in sys.modules
