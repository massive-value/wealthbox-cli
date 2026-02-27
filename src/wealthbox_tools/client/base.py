from __future__ import annotations

import asyncio
import os
import time

import httpx

BASE_URL = "https://api.crmworkspace.com/v1"


class WealthboxAPIError(Exception):
    """Raised when the Wealthbox API returns an error response."""

    def __init__(self, status_code: int, detail: str, response: httpx.Response | httpx.Request):
        self.status_code = status_code
        self.detail = detail
        self.response = response
        super().__init__(f"[{status_code}] {detail}")


class RateLimiter:
    """Async token-bucket rate limiter: sustains 1 req/sec, allows bursts."""

    def __init__(self, rate: float = 1.0):
        self._rate = rate
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            min_gap = 1.0 / self._rate
            if elapsed < min_gap:
                await asyncio.sleep(min_gap - elapsed)
            self._last_request = time.monotonic()


class _WealthboxBase:
    """Core HTTP client. Resource mixins are combined into WealthboxClient."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = BASE_URL,
        rate_limit: bool = True,
    ):
        self._token = token or os.environ.get("WEALTHBOX_TOKEN", "")
        if not self._token:
            raise ValueError(
                "Wealthbox token required. Pass token= or set WEALTHBOX_TOKEN env var."
            )
        self._rate_limiter = RateLimiter() if rate_limit else None
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"ACCESS_TOKEN": self._token},
            timeout=30.0,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> httpx.Response:
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        try:
            response = await self._http.request(method, path, params=params, json=json)
        except httpx.RequestError as exc:
            raise WealthboxAPIError(0, f"Request failed: {exc}", exc.request) from exc  # type: ignore[arg-type]

        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "5"))
            await asyncio.sleep(retry_after)
            return await self._request(method, path, params=params, json=json)

        if response.is_error:
            try:
                detail = response.json().get("error", response.text)
            except Exception:
                detail = response.text
            raise WealthboxAPIError(response.status_code, detail, response)

        return response

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "WealthboxClient":  # type: ignore[name-defined]
        return self  # type: ignore[return-value]

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
