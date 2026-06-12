from __future__ import annotations

# NOTE: As of the time these tests were written, the `wbox workflows update`
# command does not exist. There is no WorkflowUpdateInput model, no
# update_workflow() client method, and no `update` CLI subcommand under
# `workflows`. These tests document that current state and will need to be
# replaced with real update-command tests when the update command is
# implemented (Wave 3).
import json

import httpx
import respx

from wealthbox_tools.cli.main import app


def test_workflows_update_subcommand_absent(runner) -> None:
    """Invoking `workflows update` errors because the subcommand does not exist.

    This acts as a regression anchor: if someone adds the update command
    without adding tests, this test will START passing in a misleading way.
    Whoever adds the command should remove this test and replace it with
    full update-command coverage mirroring test_projects_update.py.
    """
    result = runner.invoke(app, ["workflows", "update", "1", "--label", "new-label"])
    assert result.exit_code != 0


@respx.mock
def test_complete_workflow_step_sends_put_to_step_path(runner) -> None:
    """complete-step sends PUT to /workflows/{id}/steps/{step_id}."""
    route = respx.put("https://api.crmworkspace.com/v1/workflows/1/steps/10").mock(
        return_value=httpx.Response(200, json={"id": 10, "complete": True})
    )
    # complete-step also does a follow-up GET; mock that too
    respx.get("https://api.crmworkspace.com/v1/workflows/1").mock(
        return_value=httpx.Response(
            200,
            json={"id": 1, "completed_at": None, "active_step": {"id": 11, "name": "Review"}},
        )
    )
    result = runner.invoke(app, ["workflows", "complete-step", "1", "10"])
    assert result.exit_code == 0
    assert route.calls[0].request.method == "PUT"
    sent = json.loads(route.calls[0].request.content)
    assert sent["complete"] is True


@respx.mock
def test_revert_workflow_step_sends_put_with_revert_flag(runner) -> None:
    """revert-step sends PUT to /workflows/{id}/steps/{step_id} with revert=True."""
    route = respx.put("https://api.crmworkspace.com/v1/workflows/1/steps/10").mock(
        return_value=httpx.Response(200, json={"id": 10, "reverted": True})
    )
    result = runner.invoke(app, ["workflows", "revert-step", "1", "10"])
    assert result.exit_code == 0
    assert route.calls[0].request.method == "PUT"
    sent = json.loads(route.calls[0].request.content)
    assert sent["revert"] is True


@respx.mock
def test_complete_step_with_no_advance_hint_skips_get(runner) -> None:
    """--no-advance-hint skips the follow-up GET after completing a step."""
    step_route = respx.put("https://api.crmworkspace.com/v1/workflows/1/steps/10").mock(
        return_value=httpx.Response(200, json={"id": 10, "complete": True})
    )
    result = runner.invoke(app, ["workflows", "complete-step", "1", "10", "--no-advance-hint"])
    assert result.exit_code == 0
    # The GET for the workflow should NOT have been called
    assert len(step_route.calls) == 1
    # Confirm no GET was made at all (respx would have raised if an unexpected call occurred)
