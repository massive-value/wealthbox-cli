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
