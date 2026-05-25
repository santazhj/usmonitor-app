from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings


@dataclass(frozen=True)
class MarketDataResult:
    provider: str
    status: str
    rows: dict[str, dict[str, Any]]
    eligible_count: int = 0
    loaded_count: int = 0
    detail: str = ""


_cache: dict[str, Any] = {
    "key": "",
    "expires_at": 0.0,
    "result": None,
}
_cache_lock = asyncio.Lock()


def us_snapshot_tickers(tickers: list[str]) -> list[str]:
    """Massive's stock snapshot endpoint covers U.S. symbols and ETFs."""
    return [
        ticker
        for ticker in tickers
        if ticker.replace("-", "").isalpha() and "." not in ticker
    ]


def _normalize_base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value:
        return "https://api.massive.com"
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value}"


def _timestamp_to_iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return None
    if timestamp > 10**17:
        seconds = timestamp / 1_000_000_000
    elif timestamp > 10**14:
        seconds = timestamp / 1_000_000
    else:
        seconds = timestamp / 1_000
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat()


def _number(value: Any) -> float | int | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number.is_integer():
        return int(number)
    return number


def _price(snapshot: dict[str, Any]) -> float | int | None:
    for path in (
        ("lastTrade", "p"),
        ("min", "c"),
        ("day", "c"),
        ("prevDay", "c"),
    ):
        value = snapshot
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        price = _number(value)
        if price is not None:
            return price
    return None


def normalize_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    ticker = snapshot.get("ticker")
    day = snapshot.get("day") or {}
    prev_day = snapshot.get("prevDay") or {}
    minute = snapshot.get("min") or {}
    return {
        "ticker": ticker,
        "price": _price(snapshot),
        "change": _number(snapshot.get("todaysChange")),
        "change_percent": _number(snapshot.get("todaysChangePerc")),
        "volume": _number(day.get("v") or minute.get("av") or minute.get("v")),
        "dollar_volume": _number(day.get("dv") or minute.get("dav")),
        "open": _number(day.get("o")),
        "high": _number(day.get("h")),
        "low": _number(day.get("l")),
        "close": _number(day.get("c")),
        "previous_close": _number(prev_day.get("c")),
        "updated_at": _timestamp_to_iso(snapshot.get("updated")),
        "provider": "Massive",
    }


async def fetch_massive_market_data(
    settings: Settings, tickers: list[str]
) -> MarketDataResult:
    if not settings.massive_api_key:
        return MarketDataResult(
            provider="Massive",
            status="disabled",
            rows={},
            detail="MASSIVE_API_KEY is not configured.",
        )

    eligible = us_snapshot_tickers(tickers)
    if not eligible:
        return MarketDataResult(
            provider="Massive",
            status="disabled",
            rows={},
            detail="No U.S. tickers are eligible for Massive snapshots.",
        )

    cache_key = ",".join(eligible)
    now = time.monotonic()
    async with _cache_lock:
        cached = _cache.get("result")
        if (
            _cache.get("key") == cache_key
            and cached is not None
            and float(_cache.get("expires_at", 0)) > now
        ):
            return cached

        result = await _fetch_uncached(settings, eligible)
        _cache.update(
            {
                "key": cache_key,
                "expires_at": now + max(settings.massive_cache_ttl_seconds, 1),
                "result": result,
            }
        )
        return result


async def _fetch_uncached(settings: Settings, tickers: list[str]) -> MarketDataResult:
    base_url = _normalize_base_url(settings.massive_base_url)
    full_result = await _fetch_full_snapshot(settings, base_url, tickers)
    if full_result.status == "live":
        return full_result
    if "rate limit" in full_result.detail.lower():
        return full_result

    semaphore = asyncio.Semaphore(max(settings.massive_request_concurrency, 1))
    rows: dict[str, dict[str, Any]] = {}
    errors = 0

    async with httpx.AsyncClient(base_url=base_url, timeout=12) as client:

        async def fetch_one(ticker: str) -> None:
            nonlocal errors
            async with semaphore:
                try:
                    response = await client.get(
                        f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}",
                        params={"apiKey": settings.massive_api_key},
                    )
                    if response.status_code in {400, 403, 404}:
                        errors += 1
                        return
                    response.raise_for_status()
                    payload = response.json()
                except (httpx.HTTPError, ValueError):
                    errors += 1
                    return

                snapshot = payload.get("ticker") if isinstance(payload, dict) else None
                if isinstance(snapshot, dict):
                    normalized = normalize_snapshot(snapshot)
                    if normalized.get("price") is not None:
                        rows[ticker] = normalized

        await asyncio.gather(*(fetch_one(ticker) for ticker in tickers))

    loaded = len(rows)
    status = "live" if loaded else "error"
    detail = (
        f"Massive snapshot adapter connected. {loaded}/{len(tickers)} U.S. tickers populated."
        if loaded
        else f"Massive snapshot adapter returned no usable data. {errors} requests failed."
    )
    return MarketDataResult(
        provider="Massive",
        status=status,
        rows=rows,
        eligible_count=len(tickers),
        loaded_count=loaded,
        detail=detail,
    )


async def _fetch_full_snapshot(
    settings: Settings, base_url: str, tickers: list[str]
) -> MarketDataResult:
    requested = set(tickers)
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
            response = await client.get(
                "/v2/snapshot/locale/us/markets/stocks/tickers",
                params={"apiKey": settings.massive_api_key},
            )
            if response.status_code == 429:
                return MarketDataResult(
                    provider="Massive",
                    status="error",
                    rows={},
                    eligible_count=len(tickers),
                    loaded_count=0,
                    detail="Massive snapshot rate limit exceeded.",
                )
            if response.status_code in {400, 403, 404}:
                return MarketDataResult(
                    provider="Massive",
                    status="error",
                    rows={},
                    eligible_count=len(tickers),
                    loaded_count=0,
                    detail=f"Massive full snapshot unavailable: HTTP {response.status_code}.",
                )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return MarketDataResult(
            provider="Massive",
            status="error",
            rows={},
            eligible_count=len(tickers),
            loaded_count=0,
            detail=f"Massive full snapshot request failed: {exc.__class__.__name__}.",
        )

    snapshots = payload.get("tickers") if isinstance(payload, dict) else None
    if not isinstance(snapshots, list):
        return MarketDataResult(
            provider="Massive",
            status="error",
            rows={},
            eligible_count=len(tickers),
            loaded_count=0,
            detail="Massive full snapshot returned no ticker list.",
        )

    rows: dict[str, dict[str, Any]] = {}
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        ticker = snapshot.get("ticker")
        if ticker not in requested:
            continue
        normalized = normalize_snapshot(snapshot)
        if normalized.get("price") is not None:
            rows[ticker] = normalized

    loaded = len(rows)
    status = "live" if loaded else "error"
    detail = (
        f"Massive full-market snapshot connected. {loaded}/{len(tickers)} U.S. tickers populated."
        if loaded
        else "Massive full-market snapshot returned no requested tickers."
    )
    return MarketDataResult(
        provider="Massive",
        status=status,
        rows=rows,
        eligible_count=len(tickers),
        loaded_count=loaded,
        detail=detail,
    )
