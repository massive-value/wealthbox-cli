from __future__ import annotations

from importlib.resources import as_file, files


def test_template_is_packaged_and_readable():
    resource = files("wealthbox_tools").joinpath("skills/wealthbox-crm")
    with as_file(resource) as path:
        assert path.is_dir()
        assert (path / "SKILL.md").is_file()
        assert (path / "references" / "contacts.md").is_file()


def test_skill_md_frontmatter_has_name():
    resource = files("wealthbox_tools").joinpath("skills/wealthbox-crm/SKILL.md")
    with as_file(resource) as path:
        content = path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "name: wealthbox-crm" in content


def test_bootstrap_md_is_packaged():
    resource = files("wealthbox_tools").joinpath("skills/wealthbox-crm/bootstrap.md")
    with as_file(resource) as path:
        content = path.read_text(encoding="utf-8")
    assert "wbox skills bootstrap" in content
    assert "delete" in content.lower() or "self-trim" in content.lower()


def test_firm_examples_directory_has_all_resource_files():
    resource = files("wealthbox_tools").joinpath("skills/wealthbox-crm/firm-examples")
    with as_file(resource) as path:
        names = sorted(p.name for p in path.iterdir())
    assert names == [
        "contacts.md", "events.md", "notes.md",
        "opportunities.md", "projects.md", "tasks.md", "workflows.md",
    ]


def test_old_firm_config_example_removed():
    resource = files("wealthbox_tools").joinpath("skills/wealthbox-crm")
    with as_file(resource) as path:
        assert not (path / "firm-config.example.md").exists()


def test_skill_md_has_first_run_section():
    resource = files("wealthbox_tools").joinpath("skills/wealthbox-crm/SKILL.md")
    with as_file(resource) as path:
        content = path.read_text(encoding="utf-8")
    assert "## First Run (self-delete after completion)" in content
    assert "firm/_meta.json" in content
    assert "bootstrap.md" in content


def test_skill_md_workflow_mentions_firm_folder():
    resource = files("wealthbox_tools").joinpath("skills/wealthbox-crm/SKILL.md")
    with as_file(resource) as path:
        content = path.read_text(encoding="utf-8")
    assert "firm/" in content
    assert "firm-config.md" not in content
