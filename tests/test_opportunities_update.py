from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_OPP_RESPONSE = {
    "id": 1,
    "name": "Updated Opportunity",
    "stage": 3,
    "probability": 90,
    "target_close": "2026-09-30",
}


@respx.mock
def test_update_opportunity_name(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/opportunities/1").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(app, ["opportunities", "update", "1", "--name", "Updated Opportunity"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["name"] == "Updated Opportunity"
    assert "stage" not in sent
    assert "probability" not in sent


@respx.mock
def test_update_opportunity_stage_and_probability(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/opportunities/1").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(
        app, ["opportunities", "update", "1", "--stage", "3", "--probability", "90"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["stage"] == 3
    assert sent["probability"] == 90
    assert "name" not in sent


@respx.mock
def test_update_opportunity_amounts(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/opportunities/1").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(
        app, ["opportunities", "update", "1", "--aum", "750000", "--commission", "7500"]
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    kinds = {a["kind"] for a in sent["amounts"]}
    assert "AUM" in kinds
    assert "Commission" in kinds


@respx.mock
def test_update_opportunity_link(runner) -> None:
    route = respx.put("https://api.crmworkspace.com/v1/opportunities/1").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(app, ["opportunities", "update", "1", "--contact", "30776510"])
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 30776510, "type": "Contact"}]
    assert "name" not in sent


def test_update_opportunity_empty_raises(runner) -> None:
    result = runner.invoke(app, ["opportunities", "update", "1"])
    assert result.exit_code != 0
