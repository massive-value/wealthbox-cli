from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_WORKFLOW_RESPONSE = {
    "id": 50,
    "label": "Onboarding Flow",
    "status": "active",
    "workflow_template": 7,
    "linked_to": [],
}

_STEP_RESPONSE = {
    "id": 50,
    "workflow_step": {"id": 101, "name": "Review docs", "complete": True},
}


@respx.mock
def test_add_workflow_required_template(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/workflows").mock(
        return_value=httpx.Response(200, json=_WORKFLOW_RESPONSE)
    )
    result = runner.invoke(app, ["workflows", "add", "--template", "7"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["workflow_template"] == 7


@respx.mock
def test_add_workflow_with_label_and_link(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/workflows").mock(
        return_value=httpx.Response(200, json=_WORKFLOW_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["workflows", "add", "--template", "7",
         "--label", "Onboarding Flow",
         "--contact", "30776510"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["label"] == "Onboarding Flow"
    assert sent["linked_to"] == [{"id": 30776510, "type": "Contact"}]


def test_add_workflow_missing_template(runner) -> None:
    result = runner.invoke(app, ["workflows", "add"])
    assert result.exit_code != 0


@respx.mock
def test_complete_workflow_step(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    result = runner.invoke(app, ["workflows", "complete-step", "50", "101"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["complete"] is True


@respx.mock
def test_complete_workflow_step_with_outcome(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    result = runner.invoke(
        app, ["workflows", "complete-step", "50", "101", "--outcome-id", "5"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["workflow_outcome_id"] == 5
    assert sent["complete"] is True


@respx.mock
def test_revert_workflow_step(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    result = runner.invoke(app, ["workflows", "revert-step", "50", "101"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["revert"] is True
    assert "complete" not in sent


@respx.mock
def test_list_workflow_templates(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/workflow_templates").mock(
        return_value=httpx.Response(200, json={"workflow_templates": [], "meta": {"total_count": 0}})
    )
    result = runner.invoke(app, ["workflows", "templates", "list"])
    assert result.exit_code == 0
