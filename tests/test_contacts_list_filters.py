"""
Tests for filter params on `wbox contacts list`, plus spot-checks for
`wbox tasks list` and `wbox events list`.

Design notes
============
- Server-side filters: assert the correct query param reaches the HTTP
  request by inspecting the captured respx request URL params.
- Client-side `--assigned-to`: the API ignores this param so the CLI
  calls `list_all_contacts()` (full-dataset page scan) and filters
  in-process. We verify (a) the paginating path is taken, (b) the CLI
  returns only the matching contacts, and (c) progress/warning text goes
  to *stderr*, not stdout, so stdout stays clean for piping.
- The standard `CliRunner()` already exposes `result.stdout` and `result.stderr`
  as separate attributes (Click 8.x). `result.output` is the mixed stream.
  Stream-separation tests use `result.stdout` for JSON parsing and assert
  `result.stderr` contains the progress/warning text.
"""
from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_BASE = "https://api.crmworkspace.com/v1"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _contacts_response(contacts: list[dict] | None = None) -> dict:
    return {
        "contacts": contacts or [],
        "meta": {"current_page": 1, "total_pages": 1, "total_count": len(contacts or [])},
    }


def _tasks_response(tasks: list[dict] | None = None) -> dict:
    return {
        "tasks": tasks or [],
        "meta": {"current_page": 1, "total_pages": 1, "total_count": len(tasks or [])},
    }


def _events_response(events: list[dict] | None = None) -> dict:
    return {
        "events": events or [],
        "meta": {"current_page": 1, "total_pages": 1, "total_count": len(events or [])},
    }


# ---------------------------------------------------------------------------
# Server-side filter — contacts list
# ---------------------------------------------------------------------------

@respx.mock
def test_contacts_list_filter_name(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--name", "Alice"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("name") == "Alice"


@respx.mock
def test_contacts_list_filter_email(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--email", "alice@example.com"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("email") == "alice@example.com"


@respx.mock
def test_contacts_list_filter_phone(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--phone", "555-1234"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("phone") == "555-1234"


@respx.mock
def test_contacts_list_filter_contact_type(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--contact-type", "Client"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("contact_type") == "Client"


@respx.mock
def test_contacts_list_filter_type_person(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--type", "Person"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("type") == "Person"


@respx.mock
def test_contacts_list_filter_active(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--active"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    # httpx serializes Python bools as lowercase "true"/"false"
    assert params.get("active") == "true"


@respx.mock
def test_contacts_list_filter_inactive(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--inactive"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("active") == "false"


@respx.mock
def test_contacts_list_filter_deleted(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--deleted"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("deleted") == "true"


@respx.mock
def test_contacts_list_filter_tags(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--tags", "VIP,Q1"])
    assert result.exit_code == 0, result.output
    # tags is serialized as a repeated param or list — check at least one tag
    raw_params = route.calls[0].request.url.params
    tag_values = raw_params.get_list("tags")
    assert "VIP" in tag_values
    assert "Q1" in tag_values


@respx.mock
def test_contacts_list_filter_order(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--order", "desc"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("order") == "desc"


@respx.mock
def test_contacts_list_filter_updated_since(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(
        app, ["contacts", "list", "--updated-since", "2026-01-01T00:00:00Z"]
    )
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("updated_since") == "2026-01-01T00:00:00Z"


@respx.mock
def test_contacts_list_filter_updated_before(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(
        app, ["contacts", "list", "--updated-before", "2026-06-01T00:00:00Z"]
    )
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("updated_before") == "2026-06-01T00:00:00Z"


@respx.mock
def test_contacts_list_filter_deleted_since(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(
        app, ["contacts", "list", "--deleted-since", "2026-01-01T00:00:00Z"]
    )
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("deleted_since") == "2026-01-01T00:00:00Z"


@respx.mock
def test_contacts_list_filter_household_title(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(
        app, ["contacts", "list", "--household-title", "Head"]
    )
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("household_title") == "Head"


@respx.mock
def test_contacts_list_filter_page(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--page", "2"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("page") == "2"


@respx.mock
def test_contacts_list_filter_per_page(runner) -> None:
    route = respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(200, json=_contacts_response())
    )
    result = runner.invoke(app, ["contacts", "list", "--per-page", "50"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("per_page") == "50"


# ---------------------------------------------------------------------------
# Client-side --assigned-to filter
# ---------------------------------------------------------------------------

@respx.mock
def test_contacts_list_assigned_to_filters_results(runner) -> None:
    """The CLI pages through all contacts and returns only those matching the
    given assigned_to user ID. Only one page in this test."""
    contacts = [
        {"id": 1, "name": "Alice", "type": "Person", "contact_type": "Client",
         "assigned_to": 42, "status": "Active"},
        {"id": 2, "name": "Bob", "type": "Person", "contact_type": "Client",
         "assigned_to": 99, "status": "Active"},
        {"id": 3, "name": "Carol", "type": "Person", "contact_type": "Client",
         "assigned_to": 42, "status": "Active"},
    ]
    respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(
            200,
            json={
                "contacts": contacts,
                "meta": {"total_count": 3},
            },
        )
    )

    result = runner.invoke(app, ["contacts", "list", "--assigned-to", "42"])
    assert result.exit_code == 0, result.output

    data = json.loads(result.stdout)
    returned_ids = [c["id"] for c in data["contacts"]]
    assert returned_ids == [1, 3], "Only contacts assigned to user 42 should appear"
    # Total count in the synthetic meta should also reflect the filtered set
    assert data["meta"]["total_count"] == 2


@respx.mock
def test_contacts_list_assigned_to_full_page_scan(runner) -> None:
    """With --assigned-to, the CLI must scan ALL pages (uses list_all_contacts /
    fetch_all_pages), not stop at the first page."""
    page1 = [
        {"id": i, "name": f"Contact{i}", "type": "Person", "contact_type": "Client",
         "assigned_to": 42 if i % 2 == 0 else 99, "status": "Active"}
        for i in range(1, 101)
    ]
    page2 = [
        {"id": i, "name": f"Contact{i}", "type": "Person", "contact_type": "Client",
         "assigned_to": 42, "status": "Active"}
        for i in range(101, 111)
    ]

    def _contacts_handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params.get("page", "1"))
        if page == 1:
            return httpx.Response(
                200,
                json={"contacts": page1, "meta": {"total_count": 110}},
            )
        return httpx.Response(
            200,
            json={"contacts": page2, "meta": {"total_count": 110}},
        )

    respx.get(f"{_BASE}/contacts").mock(side_effect=_contacts_handler)

    result = runner.invoke(app, ["contacts", "list", "--assigned-to", "42"])
    assert result.exit_code == 0, result.output

    data = json.loads(result.stdout)
    returned_ids = {c["id"] for c in data["contacts"]}

    # 50 even IDs from page1 (2,4,...,100) + all 10 from page2 (101-110) = 60
    expected_ids = {i for i in range(1, 101) if i % 2 == 0} | set(range(101, 111))
    assert returned_ids == expected_ids, (
        f"Expected {len(expected_ids)} contacts, got {len(returned_ids)}"
    )


@respx.mock
def test_contacts_list_assigned_to_stderr_not_stdout(runner) -> None:
    """Progress and warning messages must go to stderr; stdout must be clean JSON.

    Typer's CliRunner (Click 8.x) exposes result.stdout and result.stderr as
    separate attributes even without mix_stderr=False — stderr captures all
    output written to typer.echo(..., err=True).
    """
    contacts = [
        {"id": 1, "name": "Alice", "type": "Person", "contact_type": "Client",
         "assigned_to": 7, "status": "Active"},
    ]
    respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(
            200,
            json={"contacts": contacts, "meta": {"total_count": 1}},
        )
    )

    result = runner.invoke(app, ["contacts", "list", "--assigned-to", "7"])
    assert result.exit_code == 0

    # stdout must be parseable JSON (no stray text mixed in)
    data = json.loads(result.stdout)
    assert "contacts" in data

    # Progress/note must appear on stderr (err=True in typer.echo)
    assert result.stderr, "Expected progress/note message on stderr"
    stderr_lower = result.stderr.lower()
    assert "assigned-to" in result.stderr or "fetching" in stderr_lower or \
           "scanning" in stderr_lower or "moment" in stderr_lower, (
        f"Expected progress/note message on stderr, got: {result.stderr!r}"
    )


@respx.mock
def test_contacts_list_assigned_to_warns_when_page_also_given(runner) -> None:
    """When --page is combined with --assigned-to, a warning is sent to stderr
    and the page param is suppressed from the API request."""
    respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(
            200,
            json={"contacts": [], "meta": {"total_count": 0}},
        )
    )

    result = runner.invoke(
        app, ["contacts", "list", "--assigned-to", "5", "--page", "2"]
    )
    assert result.exit_code == 0
    # Warning should be on stderr, not stdout
    assert "--page" in result.stderr or "ignored" in result.stderr.lower()
    # stdout is still valid JSON
    json.loads(result.stdout)


@respx.mock
def test_contacts_list_assigned_to_no_match_returns_empty(runner) -> None:
    """If no contacts match the assigned_to filter, output is an empty list."""
    contacts = [
        {"id": 1, "name": "Alice", "type": "Person", "contact_type": "Client",
         "assigned_to": 99, "status": "Active"},
    ]
    respx.get(f"{_BASE}/contacts").mock(
        return_value=httpx.Response(
            200,
            json={"contacts": contacts, "meta": {"total_count": 1}},
        )
    )

    result = runner.invoke(app, ["contacts", "list", "--assigned-to", "42"])
    assert result.exit_code == 0, result.output

    data = json.loads(result.stdout)
    assert data["contacts"] == []
    assert data["meta"]["total_count"] == 0


# ---------------------------------------------------------------------------
# Spot-check: tasks list — server-side filter
# ---------------------------------------------------------------------------

@respx.mock
def test_tasks_list_filter_assigned_to(runner) -> None:
    """Tasks list passes assigned_to directly to the server (not client-side)."""
    route = respx.get(f"{_BASE}/tasks").mock(
        return_value=httpx.Response(200, json=_tasks_response())
    )
    result = runner.invoke(app, ["tasks", "list", "--assigned-to", "7"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("assigned_to") == "7"


@respx.mock
def test_tasks_list_filter_created_by(runner) -> None:
    route = respx.get(f"{_BASE}/tasks").mock(
        return_value=httpx.Response(200, json=_tasks_response())
    )
    result = runner.invoke(app, ["tasks", "list", "--created-by", "3"])
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("created_by") == "3"


# ---------------------------------------------------------------------------
# Spot-check: events list — server-side filter
# ---------------------------------------------------------------------------

@respx.mock
def test_events_list_filter_resource_id(runner) -> None:
    route = respx.get(f"{_BASE}/events").mock(
        return_value=httpx.Response(200, json=_events_response())
    )
    result = runner.invoke(
        app, ["events", "list", "--resource-id", "101", "--resource-type", "Contact"]
    )
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("resource_id") == "101"
    assert params.get("resource_type") == "Contact"


@respx.mock
def test_events_list_filter_start_date_min(runner) -> None:
    route = respx.get(f"{_BASE}/events").mock(
        return_value=httpx.Response(200, json=_events_response())
    )
    result = runner.invoke(
        app, ["events", "list", "--start-date-min", "2026-01-01"]
    )
    assert result.exit_code == 0, result.output
    params = dict(route.calls[0].request.url.params)
    assert params.get("start_date_min") == "2026-01-01"
