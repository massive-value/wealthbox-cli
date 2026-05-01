from __future__ import annotations

from wealthbox_tools.cli._skill_bootstrap import (
    render_categories_md,
    render_custom_fields_md,
    render_users_md,
)


def test_render_categories_groups_by_type():
    fetched = {
        "contact_types": [{"id": 1, "name": "Client"}, {"id": 2, "name": "Prospect"}],
        "email_types": [{"id": 10, "name": "Work"}, {"id": 11, "name": "Personal"}],
    }
    md = render_categories_md(fetched)
    assert "## contact_types" in md
    assert "## email_types" in md
    assert "Client" in md
    assert "Prospect" in md
    assert "Work" in md
    assert md.index("contact_types") < md.index("email_types")


def test_render_categories_handles_empty_type():
    md = render_categories_md({"tags": []})
    assert "## tags" in md
    assert "(no values)" in md


def test_render_categories_escapes_pipe_in_names():
    fetched = {"tags": [{"id": 1, "name": "A | B"}]}
    md = render_categories_md(fetched)
    assert "A \\| B" in md


def test_render_custom_fields_groups_by_document_type():
    fetched = {
        "Contact": [
            {"id": 1, "name": "Favorite Color", "document_type": "Contact",
             "field_type": "String", "options": []},
            {"id": 2, "name": "Risk Tolerance", "document_type": "Contact",
             "field_type": "Dropdown",
             "options": [{"label": "Low"}, {"label": "High"}]},
        ],
        "Opportunity": [
            {"id": 3, "name": "Referral Source", "document_type": "Opportunity",
             "field_type": "String", "options": []},
        ],
    }
    md = render_custom_fields_md(fetched)
    assert "## Contact" in md
    assert "## Opportunity" in md
    assert "Favorite Color" in md
    assert "Low" in md and "High" in md
    assert "Risk Tolerance" in md


def test_render_custom_fields_accepts_name_as_fallback():
    """Some API responses may use 'name' instead of 'label'; accept both."""
    fetched = {
        "Contact": [
            {"id": 1, "name": "Status", "document_type": "Contact",
             "field_type": "Dropdown",
             "options": [{"name": "Active"}, {"name": "Inactive"}]},
        ],
    }
    md = render_custom_fields_md(fetched)
    assert "Active" in md
    assert "Inactive" in md


def test_render_users_writes_table():
    users = [
        {"id": 1, "name": "Alice", "email": "a@example.com"},
        {"id": 2, "name": "Bob", "email": "b@example.com"},
    ]
    md = render_users_md(users)
    assert "| id |" in md.lower() or "| ID |" in md
    assert "Alice" in md
    assert "a@example.com" in md


def test_render_users_empty_list():
    md = render_users_md([])
    assert "(no users)" in md.lower()


# --------------------------------------------------------------------------- #
# Stubs + meta.json                                                            #
# --------------------------------------------------------------------------- #

from wealthbox_tools.cli._skill_bootstrap import (  # noqa: E402
    FIRM_README,
    STUB_CONTENTS,
    read_meta,
    update_firm_meta,
    update_template_meta,
    write_stubs,
)


def test_stub_contents_has_every_resource():
    assert set(STUB_CONTENTS) == {
        "contacts.md", "tasks.md", "notes.md", "events.md",
        "opportunities.md", "projects.md", "workflows.md",
    }


def test_each_stub_mentions_firm_examples():
    for name, body in STUB_CONTENTS.items():
        assert "firm-examples/" + name in body, f"stub {name} missing example pointer"


def test_write_stubs_creates_files_first_time(tmp_path):
    firm = tmp_path / "firm"
    firm.mkdir()
    written = write_stubs(firm)
    for name in STUB_CONTENTS:
        assert (firm / name).exists()
    assert set(written) == set(STUB_CONTENTS)


def test_write_stubs_never_overwrites(tmp_path):
    firm = tmp_path / "firm"
    firm.mkdir()
    (firm / "contacts.md").write_text("MY EDITS\n")
    written = write_stubs(firm)
    assert (firm / "contacts.md").read_text() == "MY EDITS\n"
    assert "contacts.md" not in written


def test_update_template_meta_writes_to_skill_root(tmp_path):
    update_template_meta(tmp_path, cli_version="1.1.2")
    meta = read_meta(tmp_path)
    assert meta == {"template": {"cli_version": "1.1.2"}}
    assert (tmp_path / "_meta.json").exists()


def test_update_firm_meta_preserves_template_section(tmp_path):
    update_template_meta(tmp_path, cli_version="1.1.2")
    update_firm_meta(
        tmp_path,
        identity={"id": 99, "name": "Test Firm"},
        cli_version="1.1.2",
        generated_files=["categories.md", "custom-fields.md", "users.md"],
    )
    meta = read_meta(tmp_path)
    assert meta["template"] == {"cli_version": "1.1.2"}
    assert meta["firm"]["identity"] == {"id": 99, "name": "Test Firm"}
    assert meta["firm"]["cli_version"] == "1.1.2"
    assert set(meta["firm"]["files"]) == {
        "categories.md", "custom-fields.md", "users.md",
    }
    for ts in meta["firm"]["files"].values():
        assert "T" in ts  # ISO 8601


def test_update_template_meta_preserves_firm_section(tmp_path):
    update_firm_meta(
        tmp_path,
        identity={"id": 1, "name": "Old"},
        cli_version="1.1.0",
        generated_files=["categories.md"],
    )
    update_template_meta(tmp_path, cli_version="1.1.2")
    meta = read_meta(tmp_path)
    assert meta["template"]["cli_version"] == "1.1.2"
    assert meta["firm"]["identity"]["name"] == "Old"


def test_firm_readme_constant_mentions_generated_and_hand_edited():
    assert "generated" in FIRM_README.lower()
    assert "hand-edited" in FIRM_README.lower()
