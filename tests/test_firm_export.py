"""Tests for ``wbox firm export`` and the underlying ``firm.archive.pack``."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from wealthbox_tools.cli.main import app
from wealthbox_tools.firm.archive import HAND_EDITED_FILES, pack

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _populated_firm_dir(root: Path) -> dict[str, str]:
    """Create a firm dir with one of every file we expect to encounter.

    Returns a map of filename -> body for the hand-edited files so tests can
    assert round-trip equality.
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

    # Generated files (must be excluded).
    (root / "categories.md").write_text("# generated categories\n", encoding="utf-8")
    (root / "custom-fields.md").write_text("# generated custom fields\n", encoding="utf-8")
    (root / "users.md").write_text("# generated users\n", encoding="utf-8")

    # _meta.json with both API-derived junk and the policy subset.
    (root / "_meta.json").write_text(
        json.dumps(
            {
                "identity": {"id": 100, "name": "Test Firm", "user_id": 1},
                "cli_version": "9.9.9",
                "files": {
                    "categories.md": "2024-01-01T00:00:00+00:00",
                    "custom-fields.md": "2024-01-01T00:00:00+00:00",
                    "users.md": "2024-01-01T00:00:00+00:00",
                },
                "onboarded_at": "2024-02-15T12:34:56+00:00",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return bodies


def _names_in(blob: bytes) -> set[str]:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        return set(zf.namelist())


def _read_in(blob: bytes, name: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        return zf.read(name)


# --------------------------------------------------------------------------- #
# Acceptance tests                                                             #
# --------------------------------------------------------------------------- #


def test_pack_round_trips_hand_edited_files(tmp_path: Path) -> None:
    """Round-trip — hand-edited files arrive byte-for-byte after unzip."""
    firm = tmp_path / "firm"
    bodies = _populated_firm_dir(firm)

    blob = pack(firm, now=datetime(2026, 1, 1, tzinfo=timezone.utc))

    for name, expected in bodies.items():
        assert _read_in(blob, name).decode("utf-8") == expected


def test_pack_excludes_generated_files_and_meta_api_fields(tmp_path: Path) -> None:
    """Generated files and API-derived ``_meta.json`` keys are excluded."""
    firm = tmp_path / "firm"
    _populated_firm_dir(firm)

    blob = pack(firm, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    names = _names_in(blob)

    # Generated files must not appear.
    assert "categories.md" not in names
    assert "custom-fields.md" not in names
    assert "users.md" not in names

    # _meta.json IS included, but only with the policy subset.
    assert "_meta.json" in names
    meta = json.loads(_read_in(blob, "_meta.json"))
    assert meta == {"onboarded_at": "2024-02-15T12:34:56+00:00"}
    assert "identity" not in meta
    assert "cli_version" not in meta
    assert "files" not in meta


def test_pack_does_not_include_user_prefs_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The user-prefs dir is unreachable from ``pack`` by construction.

    We mock a populated ``~/.config/wbox/user/`` and assert the resulting
    archive contains nothing under a ``user/`` path.
    """
    fake_home = tmp_path / "home"
    user_dir = fake_home / ".config" / "wbox" / "user"
    user_dir.mkdir(parents=True)
    (user_dir / "preferences.md").write_text("# secret prefs\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(fake_home / ".config"))
    monkeypatch.setenv("APPDATA", str(fake_home / ".config"))

    firm = tmp_path / "firm"
    _populated_firm_dir(firm)

    blob = pack(firm, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    names = _names_in(blob)

    assert not any(n.startswith("user/") for n in names)
    assert "preferences.md" not in names


def test_pack_manifest_has_format_version_one(tmp_path: Path) -> None:
    firm = tmp_path / "firm"
    _populated_firm_dir(firm)

    blob = pack(firm, now=datetime(2026, 1, 1, tzinfo=timezone.utc))

    manifest = json.loads(_read_in(blob, ".manifest.json"))
    assert manifest["format_version"] == 1
    assert manifest["exported_at"] == "2026-01-01T00:00:00+00:00"
    assert manifest["source_firm_name"] == "Test Firm"
    # Must come from the installed package metadata, not be empty.
    assert isinstance(manifest["source_cli_version"], str)
    assert manifest["source_cli_version"]


# --------------------------------------------------------------------------- #
# Whitelist regression                                                         #
# --------------------------------------------------------------------------- #


def test_pack_silently_drops_unexpected_files(tmp_path: Path) -> None:
    """Whitelist enforcement: a stray file in firm_dir does NOT appear in the zip.

    This guards against accidental blacklist regressions — if someone adds a
    new generated file in the future, ``pack`` keeps excluding it without
    needing the exclusion list updated.
    """
    firm = tmp_path / "firm"
    _populated_firm_dir(firm)
    (firm / "surprise.md").write_text("# I should not be in the zip\n", encoding="utf-8")
    (firm / "secret.json").write_text('{"leak": true}\n', encoding="utf-8")

    blob = pack(firm, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    names = _names_in(blob)

    assert "surprise.md" not in names
    assert "secret.json" not in names

    # Sanity: the expected whitelist is what survived (plus manifest + meta).
    assert {".manifest.json", "_meta.json"} <= names
    for name in HAND_EDITED_FILES:
        assert name in names


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #


def test_firm_export_cli_writes_zip(
    runner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The autouse isolate_config_dir fixture redirects firm_dir() under tmp_path.
    from wealthbox_tools.cli._skill_paths import firm_dir

    fd = firm_dir()
    _populated_firm_dir(fd)

    out = tmp_path / "firm.zip"
    result = runner.invoke(app, ["firm", "export", "--out", str(out)])

    assert result.exit_code == 0, result.stdout
    assert out.exists()
    blob = out.read_bytes()
    names = _names_in(blob)
    assert ".manifest.json" in names
    assert "contacts.md" in names
    assert "categories.md" not in names


def test_firm_export_cli_errors_when_firm_dir_missing(
    runner, tmp_path: Path
) -> None:
    out = tmp_path / "firm.zip"
    result = runner.invoke(app, ["firm", "export", "--out", str(out)])
    assert result.exit_code != 0
    assert not out.exists()


def test_pack_skips_symlinked_policy_files(tmp_path: Path) -> None:
    """Reject symlinked policy files so they cannot leak content from outside firm_dir.

    The whitelist trusts that ``firm_dir / name`` is a regular file under the
    firm directory. A symlink — even one pointing within firm_dir — could
    redirect to ``~/.config/wbox/user/preferences.md`` or other host content,
    breaking the "user prefs unreachable" guarantee. ``pack`` skips them.
    """
    firm = tmp_path / "firm"
    _populated_firm_dir(firm)

    # Replace contacts.md with a symlink pointing at a file outside firm_dir.
    outside = tmp_path / "outside.md"
    outside.write_text("# leaked secret content\n", encoding="utf-8")
    (firm / "contacts.md").unlink()
    try:
        (firm / "contacts.md").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform/test environment")

    blob = pack(firm, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    names = _names_in(blob)

    assert "contacts.md" not in names
    # Other whitelisted files still present.
    assert "tasks.md" in names
