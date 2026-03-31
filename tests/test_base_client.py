from __future__ import annotations

import httpx
import pytest

from wealthbox_tools.client.base import WealthboxAPIError, _WealthboxBase


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


@pytest.mark.asyncio
async def test_fetch_all_pages_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """fetch_all_pages raises WealthboxAPIError when API returns non-JSON."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=b"<html>Server Error</html>",
            headers={"content-type": "text/html"},
        )

    client = _WealthboxBase(token="test-token", rate_limit=False)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    with pytest.raises(WealthboxAPIError, match="Invalid JSON"):
        await client.fetch_all_pages("/contacts", {}, "contacts")

    await client.aclose()


@pytest.mark.asyncio
async def test_fetch_all_pages_empty_result() -> None:
    """fetch_all_pages handles empty collection gracefully."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "contacts": [],
            "meta": {"total_count": 0},
        })

    client = _WealthboxBase(token="test-token", rate_limit=False)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    result = await client.fetch_all_pages("/contacts", {}, "contacts")
    assert result == {"contacts": [], "meta": {"total_count": 0}}

    await client.aclose()


@pytest.mark.asyncio
async def test_fetch_all_pages_single_page() -> None:
    """fetch_all_pages returns all items from a single-page result."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "tasks": [{"id": 1}, {"id": 2}],
            "meta": {"total_count": 2},
        })

    client = _WealthboxBase(token="test-token", rate_limit=False)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    result = await client.fetch_all_pages("/tasks", {}, "tasks")
    assert result["tasks"] == [{"id": 1}, {"id": 2}]
    assert result["meta"]["total_count"] == 2

    await client.aclose()
