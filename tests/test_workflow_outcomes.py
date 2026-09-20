"""`wbox workflows next` surfaces the active step's outcome IDs.

`complete-step --outcome-id` is the only way to advance a step that offers
outcomes, and those IDs appear nowhere else in the CLI, so `next` has to show
them before the caller has to guess.
"""
from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app

_OUTCOMES = [
    {
        "id": 22393807,
        "name": "Provide Auto Trade Details",
        "action": "Go to Step",
        "go_to_step_id": 33410596,
        "created_at": "2025-10-29 01:37 PM -0600",
        "updated_at": "2025-10-29 01:37 PM -0600",
    },
    {
        "id": 22393808,
        "name": "Skip Enrollment",
        "action": "Complete Workflow",
        "go_to_step_id": None,
        "created_at": "2025-10-29 01:37 PM -0600",
        "updated_at": "2025-10-29 01:37 PM -0600",
    },
]

_WORKFLOW = {
    "id": 3522997,
    "name": "Auto trade enrollment",
    "completed_at": "",
    "active_step": {
        "id": 29962434,
        "name": "Populate Enrollment Info",
        "workflow_outcomes": _OUTCOMES,
    },
    "workflow_milestones": [{"id": 5, "name": "Kickoff", "milestone_date": "2026-02-01"}],
}


def _mock_get() -> None:
    respx.get("https://api.crmworkspace.com/v1/workflows/3522997").mock(
        return_value=httpx.Response(200, json=_WORKFLOW)
    )


@respx.mock
def test_next_renders_both_outcomes(runner) -> None:
    _mock_get()
    result = runner.invoke(app, ["workflows", "next", "3522997"])
    assert result.exit_code == 0
    assert '"id": 22393807' in result.stdout
    assert '"id": 22393808' in result.stdout
    assert '"go_to_step_id": 33410596' in result.stdout
    # Outcomes are slimmed to what you need to pick one.
    assert "created_at" not in result.stdout


@respx.mock
def test_next_lists_outcome_ids_on_stderr_for_every_format(runner) -> None:
    _mock_get()
    result = runner.invoke(app, ["workflows", "next", "3522997", "--format", "table"])
    assert result.exit_code == 0
    assert "complete-step --outcome-id" in result.stderr
    assert "22393807  Provide Auto Trade Details [Go to Step] -> step 33410596" in result.stderr
    assert "22393808  Skip Enrollment [Complete Workflow]" in result.stderr


@respx.mock
def test_next_stays_quiet_when_a_step_has_no_outcomes(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/workflows/1").mock(
        return_value=httpx.Response(
            200,
            json={"id": 1, "completed_at": "", "active_step": {"id": 2, "name": "Call", "workflow_outcomes": []}},
        )
    )
    result = runner.invoke(app, ["workflows", "next", "1"])
    assert result.exit_code == 0
    assert "--outcome-id" not in result.stderr


@respx.mock
def test_completed_workflow_still_reports_completion_not_outcomes(runner) -> None:
    respx.get("https://api.crmworkspace.com/v1/workflows/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "completed_at": "2026-01-02 10:00 AM -0700",
                "active_step": {"id": 2, "name": "Call", "workflow_outcomes": _OUTCOMES},
            },
        )
    )
    result = runner.invoke(app, ["workflows", "next", "1"])
    assert result.exit_code == 0
    assert '"completed": true' in result.stdout
    assert "--outcome-id" not in result.stderr


@respx.mock
def test_get_verbose_includes_milestones(runner) -> None:
    _mock_get()
    respx.get("https://api.crmworkspace.com/v1/comments").mock(
        return_value=httpx.Response(200, json={"comments": []})
    )
    result = runner.invoke(app, ["workflows", "get", "3522997", "--verbose"])
    assert result.exit_code == 0
    assert "workflow_milestones" in result.stdout
    assert "Kickoff" in result.stdout
