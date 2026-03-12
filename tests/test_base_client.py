from __future__ import annotations

import httpx
import pytest

from wealthbox_tools.client.base import _WealthboxBase, WealthboxAPIError


@pytest.mark.asyncio
async def test_request_429_retries_and_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] < 3:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"ok": True})

    client = _WealthboxBase(token="test-token", rate_limit=False, max_429_retries=5)
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.crmworkspace.com/v1")

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr("wealthbox_tools.client.base.asyncio.sleep", fake_sleep)

    response = await client._request("GET", "/tasks")
    assert response.status_code == 200
    assert calls["count"] == 3
    assert sleep_calls == [0.0, 0.0]

    await client.aclose()


@pytest.mark.asyncio
async def test_request_429_invalid_retry_after_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, headers={"Retry-After": "not-a-number"})
        return httpx.Response(200, json={"ok": True})

    client = _WealthboxBase(token="test-token", rate_limit=False, max_429_retries=3)
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.crmworkspace.com/v1")

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr("wealthbox_tools.client.base.asyncio.sleep", fake_sleep)

    response = await client._request("GET", "/tasks")
    assert response.status_code == 200
    assert sleep_calls == [5.0]

    await client.aclose()


@pytest.mark.asyncio
async def test_request_429_exceeds_retry_limit() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "0"})

    client = _WealthboxBase(token="test-token", rate_limit=False, max_429_retries=2)
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://api.crmworkspace.com/v1")

    with pytest.raises(WealthboxAPIError, match="Rate limited after 2 retries"):
        await client._request("GET", "/tasks")

    await client.aclose()
