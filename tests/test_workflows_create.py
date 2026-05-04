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
    result = runner.invoke(app, ["workflows", "complete-step", "50", "101", "--no-advance-hint"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["complete"] is True


@respx.mock
def test_complete_workflow_step_with_outcome(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    result = runner.invoke(
        app, ["workflows", "complete-step", "50", "101", "--outcome-id", "5", "--no-advance-hint"]
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
def test_complete_workflow_step_restart_with_due_date(runner) -> None:
    """`--due-date-set --due-date X` is the "Restart Step" outcome path: an
    outcome whose action restarts the same step with a fresh due date.
    Payload must carry both fields so Wealthbox knows the restart is dated."""
    route = respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["workflows", "complete-step", "50", "101",
         "--outcome-id", "9",
         "--due-date-set",
         "--due-date", "2026-05-10",
         "--no-advance-hint"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["due_date_set"] is True
    assert sent["due_date"] == "2026-05-10"
    assert sent["workflow_outcome_id"] == 9


@respx.mock
def test_workflows_next_returns_active_step(runner) -> None:
    """`wbox workflows next <ID>` is shorthand for "what do I do next?" — emits
    the active step object to stdout."""
    respx.get("https://api.crmworkspace.com/v1/workflows/50").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 50,
                "completed_at": "",
                "active_step": {
                    "id": 102, "name": "Mark AutoTrade as Pending",
                    "due_date": "2026-05-04 12:00 PM -0600",
                },
                "workflow_steps": [],
            },
        )
    )
    result = runner.invoke(app, ["workflows", "next", "50"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == 102
    assert payload["name"] == "Mark AutoTrade as Pending"


@respx.mock
def test_workflows_next_reports_completion(runner) -> None:
    """When the workflow is done, output a completion marker rather than the
    stale `active_step` (which Wealthbox does not clear)."""
    respx.get("https://api.crmworkspace.com/v1/workflows/50").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 50,
                "completed_at": "2026-05-04 10:25 AM -0600",
                # Wealthbox leaves active_step pointing at the last completed
                # step on completion — we should not echo that.
                "active_step": {"id": 999, "name": "Last step"},
                "workflow_steps": [],
            },
        )
    )
    result = runner.invoke(app, ["workflows", "next", "50"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload.get("completed") is True
    assert payload.get("completed_at") == "2026-05-04 10:25 AM -0600"


@respx.mock
def test_list_workflow_templates(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/workflow_templates").mock(
        return_value=httpx.Response(200, json={"workflow_templates": [], "meta": {"total_count": 0}})
    )
    result = runner.invoke(app, ["workflows", "templates", "list"])
    assert result.exit_code == 0


# Heavy workflow payload — `workflow_template` is what the API returns by default,
# and contains every step definition + html descriptions. We never want this in
# default `workflows list` output.
_HEAVY_LIST_RESPONSE = {
    "workflows": [
        {
            "id": 4707096,
            "label": None,
            "completed_at": "",
            "created_at": "2026-04-23 01:03 PM -0600",
            "linked_to": {"id": 30776227, "type": "Contact", "name": "Tate, Tyler & Jenny"},
            "workflow_template": {
                "id": 91540,
                "name": "Auto Trade Enrollment",
                "workflow_steps": [
                    {"name": "Step 1", "description": "x", "description_html": "<div>x</div>"},
                ] * 8,
            },
        }
    ],
    "meta": {"total_count": 1, "total_pages": 1, "page": 1},
}


@respx.mock
def test_list_workflows_default_omits_template(runner) -> None:
    """Default list output must not include the bulky workflow_template object."""
    respx.get("https://api.crmworkspace.com/v1/workflows").mock(
        return_value=httpx.Response(200, json=_HEAVY_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["workflows", "list"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    workflow = payload["workflows"][0]
    assert "workflow_template" not in workflow, (
        "workflow_template leaked into default list output (huge token waste)"
    )
    # The fields a caller actually needs for orientation must still be there.
    for field in ("id", "label", "linked_to", "created_at", "completed_at"):
        assert field in workflow, f"missing {field} from default list output"


@respx.mock
def test_list_workflows_verbose_keeps_template(runner) -> None:
    """`--verbose` must still expose the full payload including workflow_template."""
    respx.get("https://api.crmworkspace.com/v1/workflows").mock(
        return_value=httpx.Response(200, json=_HEAVY_LIST_RESPONSE)
    )
    result = runner.invoke(app, ["workflows", "list", "--verbose"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "workflow_template" in payload["workflows"][0]


def _workflow_with_active_step(active_id: int, active_name: str) -> dict:
    return {
        "id": 50,
        "completed_at": "",
        "active_step": {"id": active_id, "name": active_name},
        "workflow_steps": [],
    }


@respx.mock
def test_complete_step_emits_advance_hint_to_stderr(runner) -> None:
    """After complete-step, CLI fetches the workflow and reports the new active
    step to stderr. Stdout stays the raw API response (pipe-safe)."""
    respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/workflows/50").mock(
        return_value=httpx.Response(
            200, json=_workflow_with_active_step(102, "Mark AutoTrade as Pending")
        )
    )
    result = runner.invoke(app, ["workflows", "complete-step", "50", "101"])
    assert result.exit_code == 0
    assert "Mark AutoTrade as Pending" in result.stderr
    assert "102" in result.stderr
    # Stdout must remain pure JSON of the step response.
    json.loads(result.stdout)


@respx.mock
def test_complete_step_no_advance_hint_skips_followup(runner) -> None:
    """`--no-advance-hint` opt-out leaves stderr clean (no follow-up summary)."""
    respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/workflows/50").mock(
        return_value=httpx.Response(200, json=_workflow_with_active_step(102, "x"))
    )
    result = runner.invoke(
        app, ["workflows", "complete-step", "50", "101", "--no-advance-hint"]
    )
    assert result.exit_code == 0
    assert result.stderr == ""


_HEAVY_GET_RESPONSE = {
    "id": 4707096,
    "name": "Auto trade enrollment",
    "label": None,
    "completed_at": "",
    "started_at": "2026-04-23 01:03 PM -0600",
    "linked_to": {"id": 30776227, "type": "Contact", "name": "Tate, Tyler & Jenny"},
    "active_step": {"id": 40586028, "name": "Mark AutoTrade as Pending in SWIRL"},
    "workflow_steps": [{"id": 40586023, "name": "Populate Enrollment Info", "completed_at": "x"}],
    "workflow_template": {
        "id": 91540,
        "name": "Auto Trade Enrollment",
        "description": None,
        "description_html": None,
        "workflow_steps": [{"name": "x", "description": "y", "description_html": "<div>y</div>"}] * 8,
    },
    "comments": [],
}


@respx.mock
def test_get_workflow_default_omits_template(runner) -> None:
    """Default `get` output drops the redundant workflow_template structure.
    Template can be fetched separately via `workflows templates list`."""
    respx.get("https://api.crmworkspace.com/v1/workflows/4707096").mock(
        return_value=httpx.Response(200, json=_HEAVY_GET_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json={"comments": [], "meta": {"total_count": 0}})
    )
    result = runner.invoke(app, ["workflows", "get", "4707096"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "workflow_template" not in payload
    # Genuinely useful fields must remain.
    for field in ("id", "name", "label", "completed_at", "linked_to", "active_step", "workflow_steps"):
        assert field in payload, f"missing {field} from default get output"


@respx.mock
def test_get_workflow_verbose_keeps_template(runner) -> None:
    """`--verbose` must still expose the full payload."""
    respx.get("https://api.crmworkspace.com/v1/workflows/4707096").mock(
        return_value=httpx.Response(200, json=_HEAVY_GET_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json={"comments": [], "meta": {"total_count": 0}})
    )
    result = runner.invoke(app, ["workflows", "get", "4707096", "--verbose"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "workflow_template" in payload


@respx.mock
def test_complete_step_reports_workflow_completion(runner) -> None:
    """When the completed step terminates the workflow, the hint says so."""
    respx.put("https://api.crmworkspace.com/v1/workflows/50/steps/101").mock(
        return_value=httpx.Response(200, json=_STEP_RESPONSE)
    )
    respx.get("https://api.crmworkspace.com/v1/workflows/50").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 50,
                "completed_at": "2026-05-04 10:25 AM -0600",
                "active_step": None,
                "workflow_steps": [],
            },
        )
    )
    result = runner.invoke(app, ["workflows", "complete-step", "50", "101"])
    assert result.exit_code == 0
    assert "completed" in result.stderr.lower()
