from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app

_CONTACTS_LIST_RESPONSE = {
    "contacts": [
        {
            "id": 1,
            "name": "Alice Smith",
            "type": "Person",
            "contact_type": "Client",
            "assigned_to": 10,
            "status": "Active",
        },
        {
            "id": 2,
            "name": "Bob Jones",
            "type": "Person",
            "contact_type": "Prospect",
            "assigned_to": 11,
            "status": "Active",
        },
    ],
    "meta": {"current_page": 1, "total_pages": 1, "total_count": 5, "total_entries": 5},
}

_CONTACT_DETAIL_RESPONSE = {
    "id": 123,
    "name": "Alice Smith",
    "type": "Person",
    "contact_type": "Client",
    "assigned_to": 10,
    "status": "Active",
}

_TASKS_LIST_RESPONSE = {
    "tasks": [
        {"id": 1, "name": "Follow up", "due_date": "2026-04-01", "complete": False},
        {"id": 2, "name": "Review docs", "due_date": "2026-04-05", "complete": True},
    ],
    "meta": {"current_page": 1, "total_pages": 1, "total_count": 2, "total_entries": 2},
}

_NOTES_LIST_RESPONSE = {
    "status_updates": [
        {
            "id": 1,
            "content": "Called client",
            "linked_to": [{"id": 12, "type": "Contact"}],
            "creator_id": 5,
            "updated_at": "2025-01-01",
        },
    ],
    "meta": {"current_page": 1, "total_pages": 1, "total_count": 1, "total_entries": 1},
}


# --- table format ---

@respx.mock
def test_list_table_format_has_grid_chars(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACTS_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "list", "--format", "table"])
    assert result.exit_code == 0
    assert "+" in result.output
    assert "name" in result.output
    assert "Alice Smith" in result.output


@respx.mock
def test_get_contact_table_format_kv_layout(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/contacts/123").mock(
        return_value=httpx.Response(200, json=_CONTACT_DETAIL_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "get", "123", "--format", "table"])
    assert result.exit_code == 0
    assert "Field" in result.output
    assert "Value" in result.output
    assert "Alice Smith" in result.output


# --- csv format ---

@respx.mock
def test_list_tasks_csv_format(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASKS_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "list", "--format", "csv"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    # First line is headers
    assert "id" in lines[0]
    assert "name" in lines[0]
    # Data rows
    assert "Follow up" in result.output
    assert "Review docs" in result.output
    # No JSON brackets
    assert "{" not in result.output


# --- tsv format ---

@respx.mock
def test_list_tasks_tsv_format(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASKS_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "list", "--format", "tsv"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    # Headers should be tab-separated
    assert "\t" in lines[0]
    assert "id" in lines[0]
    assert "Follow up" in result.output


# --- nested flattening ---

@respx.mock
def test_notes_list_table_flattens_linked_to(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/notes").mock(
        return_value=httpx.Response(200, json=_NOTES_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "list", "--format", "table"])
    assert result.exit_code == 0
    # linked_to should be rendered as "Contact:12", not raw JSON
    assert "Contact:12" in result.output
    assert "[{" not in result.output


# --- total count footer ---

@respx.mock
def test_table_format_total_count_on_stderr(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACTS_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "list", "--format", "table"], catch_exceptions=False)
    assert result.exit_code == 0
    # Footer goes to stderr; typer CliRunner mixes stdout+stderr in result.output
    assert "Showing 2 of 5 results" in result.output


@respx.mock
def test_csv_format_no_footer(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/contacts").mock(
        return_value=httpx.Response(200, json=_CONTACTS_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["contacts", "list", "--format", "csv"])
    assert result.exit_code == 0
    assert "Showing" not in result.output


@respx.mock
def test_tsv_format_no_footer(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json=_TASKS_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "list", "--format", "tsv"])
    assert result.exit_code == 0
    assert "Showing" not in result.output
