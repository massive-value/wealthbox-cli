from __future__ import annotations

import logging

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


# ---------------------------------------------------------------------------
# W1.4 — edge-case coverage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_request_429_missing_retry_after_defaults_to_5s(monkeypatch: pytest.MonkeyPatch) -> None:
    """When Retry-After header is absent the client defaults to 5 s and retries."""
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            # No Retry-After header at all
            return httpx.Response(429)
        return httpx.Response(200, json={"ok": True})

    client = _WealthboxBase(token="test-token", rate_limit=False, max_429_retries=3)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr("wealthbox_tools.client.base.asyncio.sleep", fake_sleep)

    response = await client._request("GET", "/tasks")
    assert response.status_code == 200
    assert calls["count"] == 2
    # Default is 5.0 s (the get() fallback "5" parses cleanly to float)
    assert sleep_calls == [5.0]

    await client.aclose()


@pytest.mark.asyncio
async def test_request_429_very_long_malformed_retry_after_truncated_in_log(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A very long garbage Retry-After value falls back to 5 s; logged value is ≤100 chars."""
    long_garbage = "x" * 500  # far exceeds 100-char cap

    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, headers={"Retry-After": long_garbage})
        return httpx.Response(200, json={"ok": True})

    client = _WealthboxBase(token="test-token", rate_limit=False, max_429_retries=3)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    async def fake_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr("wealthbox_tools.client.base.asyncio.sleep", fake_sleep)

    with caplog.at_level(logging.WARNING, logger="wealthbox_tools.client.base"):
        response = await client._request("GET", "/tasks")

    assert response.status_code == 200
    # Falls back to the 5 s default — no crash
    assert calls["count"] == 2

    # The warning must have been emitted and the logged raw value is ≤100 chars
    warning_records = [r for r in caplog.records if "Malformed Retry-After" in r.message]
    assert warning_records, "Expected a Malformed Retry-After warning in logs"
    logged_msg = warning_records[0].message
    # The message template is:
    #   "Malformed Retry-After header %r, defaulting to 5s"
    # With %r formatting the truncated value is surrounded by quotes:
    #   "Malformed Retry-After header 'x...x', defaulting to 5s"
    # The prefix is 33 chars, suffix is 20 chars, plus 2 quote chars = 55 fixed chars.
    # The embedded raw value (between the quotes) must be ≤100 chars.
    prefix = "Malformed Retry-After header '"
    suffix = "', defaulting to 5s"
    assert logged_msg.startswith(prefix) and logged_msg.endswith(suffix)
    embedded_value = logged_msg[len(prefix) : -len(suffix)]
    assert len(embedded_value) <= 100, (
        f"Logged Retry-After value exceeds 100 chars: {len(embedded_value)}"
    )

    await client.aclose()


@pytest.mark.asyncio
async def test_request_5xx_raised_immediately_no_retry() -> None:
    """5xx responses are raised as WealthboxAPIError immediately — there is no retry."""
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(500, json={"error": "Internal Server Error"})
        # Should never reach a second call
        return httpx.Response(200, json={"ok": True})

    client = _WealthboxBase(token="test-token", rate_limit=False, max_429_retries=5)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    with pytest.raises(WealthboxAPIError) as exc_info:
        await client._request("GET", "/tasks")

    assert exc_info.value.status_code == 500
    # Only one HTTP call was made — no retry loop for 5xx
    assert calls["count"] == 1

    await client.aclose()


@pytest.mark.asyncio
async def test_request_503_raised_immediately_no_retry() -> None:
    """503 (another common 5xx) is also raised immediately without retrying."""
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(503, text="Service Unavailable")

    client = _WealthboxBase(token="test-token", rate_limit=False, max_429_retries=5)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    with pytest.raises(WealthboxAPIError) as exc_info:
        await client._request("GET", "/tasks")

    assert exc_info.value.status_code == 503
    assert calls["count"] == 1

    await client.aclose()


@pytest.mark.asyncio
async def test_fetch_all_pages_missing_collection_key_returns_empty() -> None:
    """
    When the API response is valid JSON but lacks the expected collection_key,
    fetch_all_pages treats it as an empty collection and stops after page 1.

    Behavior: data.get(collection_key, []) returns [] → len([]) < 100 → loop breaks.
    The returned dict has the key mapped to [] and meta.total_count == 0.
    """
    async def handler(request: httpx.Request) -> httpx.Response:
        # Valid JSON but the key "contacts" is absent
        return httpx.Response(200, json={"meta": {"total_count": 5}})

    client = _WealthboxBase(token="test-token", rate_limit=False)
    client._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.crmworkspace.com/v1",
    )

    result = await client.fetch_all_pages("/contacts", {}, "contacts")

    # Graceful: returns empty list, total_count reflects zero items collected
    assert result["contacts"] == []
    assert result["meta"]["total_count"] == 0

    await client.aclose()
