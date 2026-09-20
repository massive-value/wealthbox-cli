"""`--custom-field NAME=VALUE` on tasks and events.

Wealthbox only honours custom fields keyed by numeric `id`. A payload keyed by
`name` returns 200 and is silently discarded, so the CLI resolves names to IDs
and hard-fails on an unknown one.
"""
from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_CF_URL = "https://api.crmworkspace.com/v1/categories/custom_fields"
_TASK_FIELDS = {
    "custom_fields": [
        {"name": "Account Number", "id": 900, "document_type": "Task", "field_type": "text_field"},
        {"name": "Review Stage", "id": 901, "document_type": "Task", "field_type": "single_select"},
    ],
    "meta": {"total_count": 2},
}
_EVENT_FIELDS = {
    "custom_fields": [
        {"name": "Room", "id": 700, "document_type": "Event", "field_type": "text_field"}
    ],
    "meta": {"total_count": 1},
}


@respx.mock
def test_task_add_resolves_field_name_to_id(runner) -> None:
    respx.get(_CF_URL).mock(return_value=httpx.Response(200, json=_TASK_FIELDS))
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    result = runner.invoke(
        app, ["tasks", "add", "Review", "--frame", "today", "--custom-field", "Account Number=X-42"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["custom_fields"] == [{"id": 900, "value": "X-42"}]


@respx.mock
def test_task_add_accepts_a_numeric_id_without_a_lookup(runner) -> None:
    lookup = respx.get(_CF_URL).mock(return_value=httpx.Response(200, json=_TASK_FIELDS))
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    result = runner.invoke(
        app, ["tasks", "add", "Review", "--frame", "today", "--custom-field", "900=X-42"]
    )
    assert result.exit_code == 0
    assert not lookup.called
    assert json.loads(route.calls[0].request.content)["custom_fields"] == [{"id": 900, "value": "X-42"}]


@respx.mock
def test_repeated_flags_accumulate_and_values_may_contain_equals(runner) -> None:
    respx.get(_CF_URL).mock(return_value=httpx.Response(200, json=_TASK_FIELDS))
    route = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    result = runner.invoke(
        app,
        [
            "tasks", "add", "Review", "--frame", "today",
            "--custom-field", "Account Number=a=b",
            "--custom-field", "Review Stage=Final",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(route.calls[0].request.content)["custom_fields"] == [
        {"id": 900, "value": "a=b"},
        {"id": 901, "value": "Final"},
    ]


@respx.mock
def test_unknown_field_name_fails_and_lists_what_exists(runner) -> None:
    respx.get(_CF_URL).mock(return_value=httpx.Response(200, json=_TASK_FIELDS))
    post = respx.post("https://api.crmworkspace.com/v1/tasks").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    result = runner.invoke(
        app, ["tasks", "add", "Review", "--frame", "today", "--custom-field", "Nope=1"]
    )
    assert result.exit_code != 0
    assert "Account Number" in result.stderr
    assert not post.called


def test_malformed_spec_is_rejected(runner) -> None:
    result = runner.invoke(
        app, ["tasks", "add", "Review", "--frame", "today", "--custom-field", "no-equals-sign"]
    )
    assert result.exit_code != 0
    assert "NAME=VALUE" in result.stderr


@respx.mock
def test_task_update_omits_custom_fields_when_flag_absent(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json={"id": 5})
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--name", "Renamed"])
    assert result.exit_code == 0
    assert "custom_fields" not in json.loads(route.calls[0].request.content)


@respx.mock
def test_task_update_sends_resolved_custom_fields(runner) -> None:
    respx.get(_CF_URL).mock(return_value=httpx.Response(200, json=_TASK_FIELDS))
    route = respx.put("https://api.crmworkspace.com/v1/tasks/5").mock(
        return_value=httpx.Response(200, json={"id": 5})
    )
    result = runner.invoke(app, ["tasks", "update", "5", "--custom-field", "Review Stage=Final"])
    assert result.exit_code == 0
    assert json.loads(route.calls[0].request.content)["custom_fields"] == [{"id": 901, "value": "Final"}]


@respx.mock
def test_event_add_builds_the_same_payload_shape(runner) -> None:
    respx.get(_CF_URL).mock(return_value=httpx.Response(200, json=_EVENT_FIELDS))
    route = respx.post("https://api.crmworkspace.com/v1/events").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    result = runner.invoke(
        app,
        [
            "events", "add", "Review meeting",
            "--starts-at", "2026-01-15T10:00:00-07:00",
            "--ends-at", "2026-01-15T11:00:00-07:00",
            "--custom-field", "Room=Boardroom",
        ],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["custom_fields"] == [{"id": 700, "value": "Boardroom"}]
    # The lookup is scoped to the record type.
    assert "document_type=Event" in str(respx.calls[0].request.url)


@respx.mock
def test_event_update_sends_resolved_custom_fields(runner) -> None:
    respx.get(_CF_URL).mock(return_value=httpx.Response(200, json=_EVENT_FIELDS))
    route = respx.put("https://api.crmworkspace.com/v1/events/8").mock(
        return_value=httpx.Response(200, json={"id": 8})
    )
    result = runner.invoke(app, ["events", "update", "8", "--custom-field", "Room=Boardroom"])
    assert result.exit_code == 0
    assert json.loads(route.calls[0].request.content)["custom_fields"] == [{"id": 700, "value": "Boardroom"}]
