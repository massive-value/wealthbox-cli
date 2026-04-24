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
             "options": [{"name": "Low"}, {"name": "High"}]},
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
