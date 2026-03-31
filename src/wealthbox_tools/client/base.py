from __future__ import annotations

import asyncio
import collections
import json
import os
import pathlib
import time
from collections.abc import Callable
from typing import Any

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
    """Async sliding-window rate limiter: 300 requests per 5-minute window."""

    def __init__(
        self,
        rate: float = 1.0,       # kept for backward compat, unused
        window: float = 300.0,   # 5-minute window
        limit: int = 300,        # 300 req per window = 1/s average
        state_file: pathlib.Path | None = None,
    ):
        self._window = window
        self._limit = limit
        self._timestamps: collections.deque[float] = collections.deque()
        self._lock = asyncio.Lock()
        self._state_file = state_file or pathlib.Path.home() / ".wbox_rate_limit.json"
        self._load_state()

    def _load_state(self) -> None:
        try:
            raw = json.loads(self._state_file.read_text())
            wall_ts = raw.get("timestamps", [])
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return
        now_mono, now_wall = time.monotonic(), time.time()
        offset = now_mono - now_wall          # wall → monotonic
        cutoff = now_wall - self._window
        for ts in wall_ts:
            if ts > cutoff:
                self._timestamps.append(ts + offset)

    def _prune_expired(self, now: float) -> None:
        while self._timestamps and (now - self._timestamps[0]) >= self._window:
            self._timestamps.popleft()

    def _save_state(self) -> None:
        try:
            now_mono, now_wall = time.monotonic(), time.time()
            offset = now_wall - now_mono      # monotonic → wall
            cutoff = now_wall - self._window
            wall_ts = [ts + offset for ts in self._timestamps if (ts + offset) > cutoff]
            tmp = self._state_file.with_suffix(".tmp")
            tmp.write_text(json.dumps({"timestamps": wall_ts}))
            os.replace(tmp, self._state_file)  # atomic swap
        except OSError:
            pass   # never crash CLI over a cache file

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            self._prune_expired(now)
            if len(self._timestamps) >= self._limit:
                sleep_for = self._window - (now - self._timestamps[0])
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)
                self._prune_expired(time.monotonic())
            self._timestamps.append(time.monotonic())


class _WealthboxBase:
    """Core HTTP client. Resource mixins are combined into WealthboxClient."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = BASE_URL,
        rate_limit: bool = True,
        max_429_retries: int = 5,
    ):
        self._token = token or os.environ.get("WEALTHBOX_TOKEN", "")
        if not self._token:
            raise ValueError(
                "Wealthbox token required. Pass token= or set WEALTHBOX_TOKEN env var."
            )
        self._rate_limiter = RateLimiter() if rate_limit else None
        self._max_429_retries = max_429_retries
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

        retries = 0
        while True:
            try:
                response = await self._http.request(method, path, params=params, json=json)
            except httpx.RequestError as exc:
                raise WealthboxAPIError(0, f"Request failed: {exc}", exc.request) from exc  # type: ignore[arg-type]

            if response.status_code != 429:
                break

            retries += 1
            if retries > self._max_429_retries:
                raise WealthboxAPIError(
                    429,
                    f"Rate limited after {self._max_429_retries} retries.",
                    response,
                )

            try:
                retry_after = float(response.headers.get("Retry-After", "5"))
            except ValueError:
                retry_after = 5.0

            await asyncio.sleep(max(retry_after, 0.0))

        if response.is_error:
            try:
                detail = response.json().get("error", response.text)
            except Exception:
                detail = response.text
            raise WealthboxAPIError(response.status_code, detail, response)

        return response

    async def fetch_all_pages(
        self,
        path: str,
        params: dict[str, Any],
        collection_key: str,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """
        Fetch every page from a paginated list endpoint.

        Calls GET `path` with `params` (plus page/per_page overrides),
        collecting items under `collection_key` until all pages are fetched.
        Calls on_progress(page_num, total_fetched) after each page if provided.
        Returns {"<collection_key>": [...all items...], "meta": {"total_count": N}}.
        """
        all_items: list[Any] = []
        base_params = {**params, "per_page": 100}
        page = 1

        while True:
            base_params["page"] = page
            resp = await self._request("GET", path, params=base_params)
            try:
                data = resp.json()
            except Exception:
                raise WealthboxAPIError(
                    resp.status_code,
                    f"Invalid JSON in response from {path} (page {page})",
                    resp,
                )

            items = data.get(collection_key, [])
            all_items.extend(items)

            if on_progress:
                on_progress(page, len(all_items))

            total_count = data.get("meta", {}).get("total_count")
            if total_count is not None:
                if page * 100 >= total_count:
                    break
            else:
                if len(items) < 100:  # fallback if meta missing
                    break

            page += 1

        return {collection_key: all_items, "meta": {"total_count": len(all_items)}}

    async def aclose(self) -> None:
        if self._rate_limiter:
            self._rate_limiter._save_state()
        await self._http.aclose()

    async def __aenter__(self) -> "_WealthboxBase":  # type: ignore[return-value]
        return self  # type: ignore[return-value]

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
