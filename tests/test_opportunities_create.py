from __future__ import annotations

import json

import httpx
import respx

from wealthbox_tools.cli.main import app

_OPP_RESPONSE = {
    "id": 1,
    "name": "New Client AUM",
    "stage": 2,
    "probability": 75,
    "target_close": "2026-06-30",
    "manager": None,
}


@respx.mock
def test_add_opportunity_required_fields(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/opportunities").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["opportunities", "add", "New Client AUM",
         "--target-close", "2026-06-30",
         "--probability", "75",
         "--stage", "2"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["name"] == "New Client AUM"
    assert sent["probability"] == 75
    assert sent["stage"] == 2
    assert sent["target_close"] == "2026-06-30"


@respx.mock
def test_add_opportunity_with_amounts(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/opportunities").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["opportunities", "add", "New Client AUM",
         "--target-close", "2026-06-30",
         "--probability", "75",
         "--stage", "2",
         "--aum", "500000",
         "--fee", "5000",
         "--currency", "USD"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    kinds = {a["kind"] for a in sent["amounts"]}
    assert "AUM" in kinds
    assert "Fee" in kinds
    assert all(a["currency"] == "USD" for a in sent["amounts"])


@respx.mock
def test_add_opportunity_with_contact_link(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/opportunities").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["opportunities", "add", "New Client AUM",
         "--target-close", "2026-06-30",
         "--probability", "75",
         "--stage", "2",
         "--contact", "30776510"],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["linked_to"] == [{"id": 30776510, "type": "Contact"}]


@respx.mock
def test_add_opportunity_with_more_fields(runner) -> None:
    route = respx.post("https://api.crmworkspace.com/v1/opportunities").mock(
        return_value=httpx.Response(200, json=_OPP_RESPONSE)
    )
    result = runner.invoke(
        app,
        ["opportunities", "add", "New Client AUM",
         "--target-close", "2026-06-30",
         "--probability", "75",
         "--stage", "2",
         "--more-fields", '{"custom_fields": [{"id": 1, "value": "test"}]}'],
    )
    assert result.exit_code == 0
    sent = json.loads(route.calls[0].request.content)
    assert sent["custom_fields"] == [{"id": 1, "value": "test"}]


def test_add_opportunity_missing_required(runner) -> None:
    result = runner.invoke(app, ["opportunities", "add", "Missing Fields"])
    assert result.exit_code != 0


@respx.mock
def test_delete_opportunity(runner) -> None:
    respx.delete("https://api.crmworkspace.com/v1/opportunities/1").mock(
        return_value=httpx.Response(204)
    )
    result = runner.invoke(app, ["opportunities", "delete", "1"])
    assert result.exit_code == 0
    assert "1" in result.output
