"""Tests for get commands that include comments by default."""
from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app

_COMMENTS_RESPONSE = {
    "comments": [
        {
            "id": 1,
            "body": {"text": "Looks good", "html": "<div>Looks good</div>"},
            "creator": {"id": 10, "name": "Test User"},
            "created_at": "2026-03-01 10:00 AM -0700",
            "updated_at": "2026-03-01 10:00 AM -0700",
            "resource_type": "Task",
            "resource_id": 100,
        },
    ],
    "meta": {"current_page": 1, "total_pages": 1, "total_count": 1},
}

_EMPTY_COMMENTS_RESPONSE = {
    "comments": [],
    "meta": {"current_page": 1, "total_pages": 1, "total_count": 0},
}

_TASK_RESPONSE = {"id": 100, "name": "Follow up", "due_date": "2026-04-01", "complete": False}
_EVENT_RESPONSE = {"id": 200, "title": "Meeting", "starts_at": "2026-04-01T10:00:00-07:00"}
_NOTE_RESPONSE = {"id": 300, "content": "Called client", "linked_to": []}
_OPPORTUNITY_RESPONSE = {"id": 400, "name": "Big Deal", "stage": "Prospect"}
_PROJECT_RESPONSE = {"id": 500, "name": "Onboarding", "description": "New client"}
_WORKFLOW_RESPONSE = {"id": 600, "label": "Client Setup", "status": "active"}


@respx.mock
def test_task_get_includes_comments(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks/100").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "get", "100"])
    assert result.exit_code == 0
    assert '"comments"' in result.output
    assert '"text": "Looks good"' in result.output


@respx.mock
def test_task_get_no_comments_flag(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks/100").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "get", "100", "--no-comments"])
    assert result.exit_code == 0
    assert '"comments"' not in result.output


@respx.mock
def test_event_get_includes_comments(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/events/200").mock(
        return_value=httpx.Response(200, json=_EVENT_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_EMPTY_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["events", "get", "200"])
    assert result.exit_code == 0
    assert '"comments": []' in result.output


@respx.mock
def test_note_get_includes_comments(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/notes/300").mock(
        return_value=httpx.Response(200, json=_NOTE_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["notes", "get", "300"])
    assert result.exit_code == 0
    assert '"comments"' in result.output


@respx.mock
def test_opportunity_get_includes_comments(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/opportunities/400").mock(
        return_value=httpx.Response(200, json=_OPPORTUNITY_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_EMPTY_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["opportunities", "get", "400"])
    assert result.exit_code == 0
    assert '"comments"' in result.output


@respx.mock
def test_project_get_includes_comments(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/projects/500").mock(
        return_value=httpx.Response(200, json=_PROJECT_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["projects", "get", "500"])
    assert result.exit_code == 0
    assert '"comments"' in result.output


@respx.mock
def test_workflow_get_includes_comments(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/workflows/600").mock(
        return_value=httpx.Response(200, json=_WORKFLOW_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_EMPTY_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["workflows", "get", "600"])
    assert result.exit_code == 0
    assert '"comments"' in result.output


@respx.mock
def test_task_get_table_shows_comment_count_and_preview(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks/100").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "get", "100", "--format", "table"])
    assert result.exit_code == 0
    assert "comment_count" in result.output
    assert "latest_comment" in result.output
    assert "1" in result.output  # count
    assert "Looks good" in result.output  # preview


@respx.mock
def test_task_get_table_empty_comments(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks/100").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_EMPTY_COMMENTS_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "get", "100", "--format", "table"])
    assert result.exit_code == 0
    assert "comment_count" in result.output
    assert "0" in result.output


@respx.mock
def test_task_get_table_no_comments_flag_omits_columns(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/tasks/100").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    result = runner.invoke(app, ["tasks", "get", "100", "--format", "table", "--no-comments"])
    assert result.exit_code == 0
    assert "comment_count" not in result.output
    assert "latest_comment" not in result.output


@respx.mock
def test_comments_query_params_sent_correctly(runner) -> None:
    """Verify the comments request uses the correct resource_type and resource_id."""
    respx.get("https://api.crmworkspace.com/v1/tasks/100").mock(
        return_value=httpx.Response(200, json=_TASK_RESPONSE)
    )
    route = respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json=_EMPTY_COMMENTS_RESPONSE)
    )
    runner.invoke(app, ["tasks", "get", "100"])
    assert route.called
    request = route.calls.last.request
    assert "resource_type=Task" in str(request.url)
    assert "resource_id=100" in str(request.url)
