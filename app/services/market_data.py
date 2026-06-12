from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, time as dt_time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.config import Settings


PRIVATE_REST_BASE_URL = "http://api.massiveprivateserver.site"


@dataclass(frozen=True)
class MarketDataResult:
    provider: str
    status: str
    rows: dict[str, dict[str, Any]]
    eligible_count: int = 0
    loaded_count: int = 0
    fundamentals_loaded_count: int = 0
    detail: str = ""


_cache: dict[str, Any] = {
    "key": "",
    "expires_at": 0.0,
    "result": None,
}
_cache_lock = asyncio.Lock()
_fundamentals_cache: dict[str, Any] = {
    "key": "",
    "expires_at": 0.0,
    "rows": {},
}
_yahoo_cache: dict[str, Any] = {
    "key": "",
    "expires_at": 0.0,
    "rows": {},
}
_yahoo_fundamentals_cache: dict[str, Any] = {
    "key": "",
    "expires_at": 0.0,
    "rows": {},
}
_candle_cache: dict[str, Any] = {}
_candle_cache_lock = asyncio.Lock()

CANDLE_PERIODS: dict[str, dict[str, Any]] = {
    "intraday": {
        "multiplier": 5,
        "timespan": "minute",
        "days": 5,
        "limit": 500,
        "yahoo_range": "1d",
        "yahoo_interval": "5m",
    },
    "day": {
        "multiplier": 1,
        "timespan": "day",
        "days": 365,
        "limit": 500,
        "yahoo_range": "1y",
        "yahoo_interval": "1d",
    },
    "week": {
        "multiplier": 1,
        "timespan": "week",
        "days": 365 * 3,
        "limit": 500,
        "yahoo_range": "5y",
        "yahoo_interval": "1wk",
    },
    "month": {
        "multiplier": 1,
        "timespan": "month",
        "days": 365 * 8,
        "limit": 500,
        "yahoo_range": "10y",
        "yahoo_interval": "1mo",
    },
    "year": {
        "multiplier": 1,
        "timespan": "year",
        "days": 365 * 20,
        "limit": 500,
        "yahoo_range": "max",
        "yahoo_interval": "1mo",
    },
}

# Last-resort low-frequency fundamentals for global watchlist names. These keep
# the dashboard useful when Yahoo's crumb-gated quote endpoint is unavailable
# from the production host.
STATIC_GLOBAL_FUNDAMENTALS: dict[str, dict[str, Any]] = {
    "000660.KS": {
        "market_cap": 1_377_828_327_129_088,
        "pe_ratio": 6.568369,
        "fundamentals_currency": "KRW",
    },
    "005930.KS": {
        "market_cap": 1_920_719_709_536_256,
        "pe_ratio": 6.648751,
        "fundamentals_currency": "KRW",
    },
    "2802.T": {
        "market_cap": 5_225_828_581_376,
        "pe_ratio": 39.478058,
        "fundamentals_currency": "JPY",
    },
    "3037.TW": {
        "market_cap": 1_558_774_153_216,
        "pe_ratio": 227.06421,
        "fundamentals_currency": "TWD",
    },
    "4062.T": {
        "market_cap": 5_862_759_858_176,
        "pe_ratio": 97.3794,
        "fundamentals_currency": "JPY",
    },
    "6857.T": {
        "market_cap": 20_187_493_433_344,
        "pe_ratio": 54.277023,
        "fundamentals_currency": "JPY",
    },
    "ATS.VI": {
        "market_cap": 5_081_580_032,
        "pe_ratio": 39.636364,
        "fundamentals_currency": "EUR",
    },
    "BESI.AS": {
        "market_cap": 21_673_144_320,
        "pe_ratio": 142.5,
        "fundamentals_currency": "EUR",
    },
    "IQE.L": {
        "market_cap": 448_296_128,
        "pe_note": "N/M",
        "eps_trailing_twelve_months": -0.05,
        "fundamentals_currency": "GBP",
    },
    "SIVE.ST": {
        "market_cap": 21_617_383_424,
        "pe_note": "N/M",
        "eps_trailing_twelve_months": -0.81,
        "fundamentals_currency": "SEK",
    },
    "SOI.PA": {
        "market_cap": 6_334_940_160,
        "pe_ratio": 633.3929,
        "fundamentals_currency": "EUR",
    },
    "SU.PA": {
        "market_cap": 151_380_787_200,
        "pe_ratio": 33.80025,
        "fundamentals_currency": "EUR",
    },
}


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
        return PRIVATE_REST_BASE_URL
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


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
        if price is not None and price > 0:
            return price
    return None


def _price_mode(snapshot: dict[str, Any]) -> str:
    for path, mode in (
        (("lastTrade", "p"), "live"),
        (("min", "c"), "live"),
        (("day", "c"), "close"),
        (("prevDay", "c"), "close"),
    ):
        value = snapshot
        for key in path:
            value = value.get(key) if isinstance(value, dict) else None
        price = _number(value)
        if price is not None and price > 0:
            return mode
    return "missing"


def _market_schedule(ticker: str | None, exchange: str | None) -> tuple[str, dt_time, dt_time] | None:
    ticker = (ticker or "").upper()
    exchange = (exchange or "").upper()
    if ticker.endswith(".KS") or exchange in {"KSC", "KOE"}:
        return ("Asia/Seoul", dt_time(9, 0), dt_time(15, 30))
    if ticker.endswith(".T") or exchange in {"JPX", "JP", "JPN"}:
        return ("Asia/Tokyo", dt_time(9, 0), dt_time(15, 30))
    if ticker.endswith(".TW") or exchange in {"TAI", "TWO"}:
        return ("Asia/Taipei", dt_time(9, 0), dt_time(13, 30))
    if ticker.endswith(".AS") or exchange in {"AMS"}:
        return ("Europe/Amsterdam", dt_time(9, 0), dt_time(17, 30))
    if ticker.endswith(".PA") or exchange in {"PAR"}:
        return ("Europe/Paris", dt_time(9, 0), dt_time(17, 30))
    if ticker.endswith(".VI") or exchange in {"VIE"}:
        return ("Europe/Vienna", dt_time(9, 0), dt_time(17, 30))
    if ticker.endswith(".ST") or exchange in {"STO"}:
        return ("Europe/Stockholm", dt_time(9, 0), dt_time(17, 30))
    if ticker.endswith(".L") or exchange in {"LSE", "LSEIOB"}:
        return ("Europe/London", dt_time(8, 0), dt_time(16, 30))
    if ticker and "." not in ticker:
        return ("America/New_York", dt_time(9, 30), dt_time(16, 0))
    return None


def _regular_session_price_mode(
    ticker: str | None,
    exchange: str | None,
    updated_at: str | None,
    now_utc: datetime | None = None,
) -> str:
    schedule = _market_schedule(ticker, exchange)
    if not schedule:
        return "close"
    timezone_name, open_time, close_time = schedule
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    market_tz = ZoneInfo(timezone_name)
    local_now = now.astimezone(market_tz)
    if local_now.weekday() >= 5:
        return "close"
    if not (open_time <= local_now.time() <= close_time):
        return "close"
    updated = _parse_iso_datetime(updated_at)
    if updated:
        local_updated = updated.astimezone(market_tz)
        if local_updated.date() != local_now.date():
            return "close"
        if (now - updated).total_seconds() > 45 * 60:
            return "close"
    return "live"


def normalize_snapshot(snapshot: dict[str, Any], now_utc: datetime | None = None) -> dict[str, Any]:
    ticker = snapshot.get("ticker")
    day = snapshot.get("day") or {}
    prev_day = snapshot.get("prevDay") or {}
    minute = snapshot.get("min") or {}
    price = _price(snapshot)
    volume = _number(day.get("v") or minute.get("av") or minute.get("v"))
    vwap = _number(day.get("vw") or minute.get("vw"))
    raw_dollar_volume = _number(day.get("dv") or minute.get("dav"))
    dollar_volume = raw_dollar_volume
    if volume and (vwap or price):
        computed_dollar_volume = volume * (vwap or price)
        if dollar_volume is None or dollar_volume <= volume * 10:
            dollar_volume = computed_dollar_volume
    updated_at = _timestamp_to_iso(snapshot.get("updated"))
    raw_price_mode = _price_mode(snapshot)
    return {
        "ticker": ticker,
        "price": price,
        "change": _number(snapshot.get("todaysChange")),
        "change_percent": _number(snapshot.get("todaysChangePerc")),
        "volume": volume,
        "dollar_volume": dollar_volume,
        "open": _number(day.get("o")),
        "high": _number(day.get("h")),
        "low": _number(day.get("l")),
        "close": _number(day.get("c")),
        "previous_close": _number(prev_day.get("c")),
        "updated_at": updated_at,
        "price_mode": (
            "missing"
            if raw_price_mode == "missing"
            else _regular_session_price_mode(ticker, None, updated_at, now_utc)
        ),
        "provider": "Massive",
    }


def normalize_aggregate_candles(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return []
    rows = []
    for item in results:
        if not isinstance(item, dict):
            continue
        opened = _number(item.get("o"))
        high = _number(item.get("h"))
        low = _number(item.get("l"))
        close = _number(item.get("c"))
        timestamp = item.get("t")
        if opened is None or high is None or low is None or close is None or timestamp is None:
            continue
        try:
            seconds = int(timestamp) / 1000
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(),
                "open": opened,
                "high": high,
                "low": low,
                "close": close,
                "volume": _number(item.get("v")),
                "vwap": _number(item.get("vw")),
            }
        )
    return rows


def _aggregate_yearly_candles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        parsed = _parse_iso_datetime(row.get("timestamp"))
        if not parsed:
            continue
        buckets.setdefault(parsed.year, []).append(row)
    yearly = []
    for year in sorted(buckets):
        items = buckets[year]
        highs = [item["high"] for item in items if item.get("high") is not None]
        lows = [item["low"] for item in items if item.get("low") is not None]
        volumes = [item.get("volume") or 0 for item in items]
        if not highs or not lows:
            continue
        yearly.append(
            {
                "timestamp": items[0]["timestamp"],
                "open": items[0]["open"],
                "high": max(highs),
                "low": min(lows),
                "close": items[-1]["close"],
                "volume": sum(volumes) if volumes else None,
                "vwap": None,
            }
        )
    return yearly


def normalize_yahoo_candles(payload: dict[str, Any], period: str) -> list[dict[str, Any]]:
    chart = payload.get("chart") if isinstance(payload, dict) else None
    results = chart.get("result") if isinstance(chart, dict) else None
    if not isinstance(results, list) or not results:
        return []
    result = results[0]
    timestamps = result.get("timestamp") if isinstance(result, dict) else None
    indicators = result.get("indicators") if isinstance(result, dict) else {}
    quote_list = indicators.get("quote") if isinstance(indicators, dict) else None
    quote = quote_list[0] if isinstance(quote_list, list) and quote_list else {}
    if not isinstance(timestamps, list) or not isinstance(quote, dict):
        return []
    rows = []
    for index, timestamp in enumerate(timestamps):
        try:
            seconds = int(timestamp)
        except (TypeError, ValueError):
            continue
        opened = _number((quote.get("open") or [None])[index] if index < len(quote.get("open") or []) else None)
        high = _number((quote.get("high") or [None])[index] if index < len(quote.get("high") or []) else None)
        low = _number((quote.get("low") or [None])[index] if index < len(quote.get("low") or []) else None)
        close = _number((quote.get("close") or [None])[index] if index < len(quote.get("close") or []) else None)
        if opened is None or high is None or low is None or close is None:
            continue
        volume_values = quote.get("volume") or []
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat(),
                "open": opened,
                "high": high,
                "low": low,
                "close": close,
                "volume": _number(volume_values[index]) if index < len(volume_values) else None,
                "vwap": None,
            }
        )
    return _aggregate_yearly_candles(rows) if period == "year" else rows


def _field_value(block: dict[str, Any], field: str) -> float | int | None:
    node = block.get(field)
    if isinstance(node, dict):
        return _number(node.get("value"))
    return None


def normalize_ticker_overview(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(result, dict):
        return {}
    return {
        "market_cap": _positive_number(result.get("market_cap")),
        "weighted_shares_outstanding": _number(result.get("weighted_shares_outstanding")),
    }


def normalize_financials(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        return {}
    first = results[0]
    financials = first.get("financials") if isinstance(first, dict) else None
    if not isinstance(financials, dict):
        return {}
    income = financials.get("income_statement") or {}
    diluted_eps = _field_value(income, "diluted_earnings_per_share")
    basic_eps = _field_value(income, "basic_earnings_per_share")
    return {
        "ttm_diluted_eps": diluted_eps,
        "ttm_basic_eps": basic_eps,
        "financial_period": first.get("fiscal_period"),
        "financial_end_date": first.get("end_date"),
    }


def _last_number(values: list[Any] | None) -> float | int | None:
    if not values:
        return None
    for value in reversed(values):
        number = _number(value)
        if number is not None:
            return number
    return None


def _previous_number(values: list[Any] | None) -> float | int | None:
    if not values:
        return None
    found_last = False
    for value in reversed(values):
        number = _number(value)
        if number is None:
            continue
        if found_last:
            return number
        found_last = True
    return None


def normalize_yahoo_chart(
    payload: dict[str, Any],
    ticker: str,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    chart = payload.get("chart") if isinstance(payload, dict) else None
    results = chart.get("result") if isinstance(chart, dict) else None
    if not isinstance(results, list) or not results:
        return {}
    result = results[0]
    meta = result.get("meta") if isinstance(result, dict) else {}
    indicators = result.get("indicators") or {}
    quote_list = indicators.get("quote") or []
    quote = quote_list[0] if quote_list else {}

    closes = quote.get("close")
    price = _number(meta.get("regularMarketPrice")) or _last_number(closes)
    previous_close = _previous_number(closes) or _number(meta.get("previousClose")) or _number(
        meta.get("chartPreviousClose")
    )
    volume = _number(meta.get("regularMarketVolume")) or _last_number(
        quote.get("volume")
    )
    change = price - previous_close if price is not None and previous_close else None
    change_percent = (
        (change / previous_close) * 100
        if change is not None and previous_close
        else None
    )
    timestamp = meta.get("regularMarketTime")
    updated_at = None
    if timestamp:
        try:
            updated_at = datetime.fromtimestamp(
                int(timestamp), tz=timezone.utc
            ).isoformat()
        except (TypeError, ValueError, OSError):
            updated_at = None

    if price is None or price <= 0:
        return {}
    market_state = str(meta.get("marketState") or "").upper()
    exchange = meta.get("exchangeName")
    if market_state == "REGULAR":
        price_mode = "live"
    elif market_state in {"PRE", "POST", "POSTPOST", "PREPRE", "CLOSED"}:
        price_mode = "close"
    else:
        price_mode = _regular_session_price_mode(ticker, exchange, updated_at, now_utc)

    return {
        "ticker": ticker,
        "price": price,
        "change": change,
        "change_percent": change_percent,
        "volume": volume,
        "dollar_volume": volume * price if volume and price else None,
        "open": _last_number(quote.get("open")),
        "high": _last_number(quote.get("high")),
        "low": _last_number(quote.get("low")),
        "close": _last_number(quote.get("close")),
        "previous_close": previous_close,
        "updated_at": updated_at,
        "currency": meta.get("currency"),
        "exchange": exchange,
        "price_mode": price_mode,
        "provider": "Yahoo Chart",
    }


def _positive_number(*values: Any) -> float | int | None:
    for value in values:
        number = _number(value)
        if number is not None and number > 0:
            return number
    return None


def normalize_yahoo_quote_item(item: dict[str, Any]) -> dict[str, Any]:
    ticker = item.get("symbol")
    if not ticker:
        return {}

    market_cap = _positive_number(item.get("marketCap"))
    shares = _number(item.get("sharesOutstanding")) or _number(
        item.get("impliedSharesOutstanding")
    )
    price = _number(item.get("regularMarketPrice"))
    quote_currency = item.get("currency")
    financial_currency = item.get("financialCurrency") or quote_currency
    if market_cap is None and shares and price:
        price_for_market_cap = price
        if quote_currency in {"GBp", "GBX"} and financial_currency == "GBP":
            price_for_market_cap = price / 100
        market_cap = shares * price_for_market_cap

    pe_ratio = _positive_number(
        item.get("trailingPE"),
        item.get("priceEpsCurrentYear"),
        item.get("forwardPE"),
    )
    pe_note = None
    if pe_ratio is None:
        trailing_eps = _number(item.get("epsTrailingTwelveMonths"))
        current_year_eps = _number(item.get("epsCurrentYear"))
        if (trailing_eps is not None and trailing_eps <= 0) or (
            current_year_eps is not None and current_year_eps <= 0
        ):
            pe_note = "N/M"

    row = {
        "ticker": ticker,
        "market_cap": market_cap,
        "weighted_shares_outstanding": shares,
        "pe_ratio": pe_ratio,
        "pe_note": pe_note,
        "trailing_pe": _number(item.get("trailingPE")),
        "forward_pe": _number(item.get("forwardPE")),
        "price_eps_current_year": _number(item.get("priceEpsCurrentYear")),
        "eps_trailing_twelve_months": _number(item.get("epsTrailingTwelveMonths")),
        "eps_current_year": _number(item.get("epsCurrentYear")),
        "fundamentals_currency": financial_currency,
        "fundamentals_provider": "Yahoo Quote",
    }
    return {
        key: value
        for key, value in row.items()
        if value is not None and value != ""
    }


def normalize_yahoo_quote(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    quote_response = payload.get("quoteResponse") if isinstance(payload, dict) else None
    results = quote_response.get("result") if isinstance(quote_response, dict) else None
    if not isinstance(results, list):
        return {}
    rows = {}
    for item in results:
        if not isinstance(item, dict):
            continue
        normalized = normalize_yahoo_quote_item(item)
        ticker = normalized.get("ticker")
        if ticker:
            rows[ticker] = normalized
    return rows


def static_global_fundamentals(tickers: list[str]) -> dict[str, dict[str, Any]]:
    rows = {}
    for ticker in dict.fromkeys(tickers):
        fallback = STATIC_GLOBAL_FUNDAMENTALS.get(ticker)
        if fallback:
            rows[ticker] = {
                **fallback,
                "ticker": ticker,
                "fundamentals_provider": "Static Global Fundamentals",
            }
    return rows


async def fetch_dashboard_market_data(
    settings: Settings, tickers: list[str]
) -> MarketDataResult:
    massive = await fetch_massive_market_data(settings, tickers)
    rows = {ticker: dict(row) for ticker, row in massive.rows.items()}
    missing = [ticker for ticker in tickers if ticker not in rows]
    yahoo_rows = await fetch_yahoo_chart_market_data(settings, missing)
    for ticker, row in yahoo_rows.items():
        rows.setdefault(ticker, dict(row))

    if rows:
        yahoo_loaded = len([ticker for ticker in yahoo_rows if ticker in rows])
        fundamentals_needed = [
            ticker
            for ticker, row in rows.items()
            if row.get("market_cap") is None or row.get("pe_ratio") is None
        ]
        yahoo_fundamentals = await fetch_yahoo_quote_fundamentals(
            settings, fundamentals_needed
        )
        yahoo_fundamentals_loaded = 0
        for ticker, fundamentals in yahoo_fundamentals.items():
            row = rows.get(ticker)
            if row is None:
                continue
            before = (row.get("market_cap"), row.get("pe_ratio"), row.get("pe_note"))
            for key, value in fundamentals.items():
                if key == "ticker":
                    continue
                if key in {"market_cap", "pe_ratio", "pe_note"}:
                    if row.get(key) is None and value is not None:
                        row[key] = value
                else:
                    row.setdefault(key, value)
            after = (row.get("market_cap"), row.get("pe_ratio"), row.get("pe_note"))
            if after != before:
                yahoo_fundamentals_loaded += 1

        static_needed = [
            ticker
            for ticker, row in rows.items()
            if row.get("market_cap") is None
            or (row.get("pe_ratio") is None and row.get("pe_note") is None)
        ]
        static_fundamentals = static_global_fundamentals(static_needed)
        static_fundamentals_loaded = 0
        for ticker, fundamentals in static_fundamentals.items():
            row = rows.get(ticker)
            if row is None:
                continue
            before = (row.get("market_cap"), row.get("pe_ratio"), row.get("pe_note"))
            for key, value in fundamentals.items():
                if key == "ticker":
                    continue
                if key in {"market_cap", "pe_ratio", "pe_note", "fundamentals_provider"}:
                    if row.get(key) is None and value is not None:
                        row[key] = value
                else:
                    row.setdefault(key, value)
            after = (row.get("market_cap"), row.get("pe_ratio"), row.get("pe_note"))
            if after != before:
                static_fundamentals_loaded += 1

        fundamentals_loaded = sum(
            1
            for row in rows.values()
            if row.get("market_cap") is not None
            or row.get("pe_ratio") is not None
            or row.get("pe_note") is not None
        )
        yahoo_fundamentals_available = sum(
            1
            for row in rows.values()
            if row.get("fundamentals_provider") == "Yahoo Quote"
            and (
                row.get("market_cap") is not None
                or row.get("pe_ratio") is not None
                or row.get("pe_note") is not None
            )
        )
        static_fundamentals_available = sum(
            1
            for row in rows.values()
            if row.get("fundamentals_provider") == "Static Global Fundamentals"
            and (
                row.get("market_cap") is not None
                or row.get("pe_ratio") is not None
                or row.get("pe_note") is not None
            )
        )
        detail = massive.detail
        if yahoo_loaded:
            detail = (
                f"{detail} Yahoo Chart fallback populated "
                f"{yahoo_loaded}/{len(missing)} missing/global tickers."
            )
        if yahoo_fundamentals_loaded or yahoo_fundamentals_available:
            detail = (
                f"{detail} Yahoo Quote fundamentals populated "
                f"{yahoo_fundamentals_available}/{len(rows)} "
                "market-cap/PE rows."
            )
        if static_fundamentals_loaded or static_fundamentals_available:
            detail = (
                f"{detail} Static global fundamentals fallback populated "
                f"{static_fundamentals_available}/{len(rows)} market-cap/PE rows."
            )
        provider_parts = ["Massive"]
        if yahoo_loaded:
            provider_parts.append("Yahoo Chart")
        if yahoo_fundamentals_available:
            provider_parts.append("Yahoo Quote")
        if static_fundamentals_available:
            provider_parts.append("Static Fundamentals")
        return MarketDataResult(
            provider=" + ".join(provider_parts),
            status="live",
            rows=rows,
            eligible_count=len(tickers),
            loaded_count=len(rows),
            fundamentals_loaded_count=fundamentals_loaded,
            detail=detail,
        )

    return massive


async def fetch_market_candles(
    settings: Settings,
    ticker: str,
    period: str,
) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    period = period.strip().lower()
    if period not in CANDLE_PERIODS:
        raise ValueError("Unsupported candle period.")

    cache_key = f"{ticker}:{period}"
    now = time.monotonic()
    async with _candle_cache_lock:
        cached = _candle_cache.get(cache_key)
        if cached and float(cached.get("expires_at", 0)) > now:
            return cached["payload"]

    rows: list[dict[str, Any]] = []
    source = ""
    detail = ""
    if settings.massive_api_key:
        rows, detail = await _fetch_massive_candles(settings, ticker, period)
        if rows:
            source = "massive"

    if not rows:
        fallback_rows, fallback_detail = await _fetch_yahoo_candles(ticker, period)
        if fallback_rows:
            rows = fallback_rows
            source = "fallback"
            detail = fallback_detail
        elif not detail:
            detail = fallback_detail or "No candle data returned."

    payload = {
        "ticker": ticker,
        "period": period,
        "status": "ok" if rows else "empty",
        "source": source,
        "detail": detail,
        "candles": rows,
    }
    ttl = 60 if period == "intraday" else 15 * 60
    async with _candle_cache_lock:
        _candle_cache[cache_key] = {"expires_at": now + ttl, "payload": payload}
    return payload


async def _fetch_massive_candles(
    settings: Settings,
    ticker: str,
    period: str,
) -> tuple[list[dict[str, Any]], str]:
    config = CANDLE_PERIODS[period]
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=int(config["days"]))
    base_url = _normalize_base_url(settings.massive_base_url)
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=20) as client:
            response = await client.get(
                f"/v2/aggs/ticker/{ticker}/range/{config['multiplier']}/{config['timespan']}/{start}/{end}",
                params={
                    "adjusted": "true",
                    "sort": "asc",
                    "limit": int(config["limit"]),
                    "apiKey": settings.massive_api_key,
                },
            )
            if response.status_code in {400, 403, 404}:
                return [], f"Massive candles unavailable: HTTP {response.status_code}."
            response.raise_for_status()
            rows = normalize_aggregate_candles(response.json())
            return rows, (
                f"Massive returned {len(rows)} candles."
                if rows
                else "Massive returned no candles for this ticker/period."
            )
    except (httpx.HTTPError, ValueError) as exc:
        return [], f"Massive candles request failed: {exc.__class__.__name__}."


async def _fetch_yahoo_candles(ticker: str, period: str) -> tuple[list[dict[str, Any]], str]:
    config = CANDLE_PERIODS[period]
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            response = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                params={
                    "range": config["yahoo_range"],
                    "interval": config["yahoo_interval"],
                    "includePrePost": "false",
                },
            )
            if response.status_code != 200:
                return [], f"Fallback candles unavailable: HTTP {response.status_code}."
            rows = normalize_yahoo_candles(response.json(), period)
            return rows, (
                f"Fallback returned {len(rows)} candles."
                if rows
                else "No candle data returned."
            )
    except (httpx.HTTPError, ValueError) as exc:
        return [], f"Fallback candles request failed: {exc.__class__.__name__}."


async def fetch_yahoo_chart_market_data(
    settings: Settings, tickers: list[str]
) -> dict[str, dict[str, Any]]:
    requested = [ticker for ticker in dict.fromkeys(tickers) if ticker]
    if not requested:
        return {}

    cache_key = ",".join(requested)
    now = time.monotonic()
    cached = _yahoo_cache.get("rows")
    if (
        _yahoo_cache.get("key") == cache_key
        and isinstance(cached, dict)
        and float(_yahoo_cache.get("expires_at", 0)) > now
    ):
        return cached

    rows = await _fetch_yahoo_chart_uncached(settings, requested)
    _yahoo_cache.update(
        {
            "key": cache_key,
            "expires_at": now + max(settings.massive_cache_ttl_seconds, 30),
            "rows": rows,
        }
    )
    return rows


async def _fetch_yahoo_chart_uncached(
    settings: Settings, tickers: list[str]
) -> dict[str, dict[str, Any]]:
    semaphore = asyncio.Semaphore(max(settings.massive_request_concurrency, 1))
    rows: dict[str, dict[str, Any]] = {}
    headers = {"User-Agent": "Mozilla/5.0"}

    async with httpx.AsyncClient(
        base_url="https://query1.finance.yahoo.com", timeout=12, headers=headers
    ) as client:

        async def fetch_one(ticker: str) -> None:
            async with semaphore:
                try:
                    response = await client.get(
                        f"/v8/finance/chart/{ticker}",
                        params={"range": "5d", "interval": "1d"},
                    )
                    if response.status_code != 200:
                        return
                    normalized = normalize_yahoo_chart(response.json(), ticker)
                except (httpx.HTTPError, ValueError):
                    return
                if normalized:
                    rows[ticker] = normalized

        await asyncio.gather(*(fetch_one(ticker) for ticker in tickers))

    return rows


async def fetch_yahoo_quote_fundamentals(
    settings: Settings, tickers: list[str]
) -> dict[str, dict[str, Any]]:
    requested = [ticker for ticker in dict.fromkeys(tickers) if ticker]
    if not requested:
        return {}

    cache_key = ",".join(requested)
    now = time.monotonic()
    cached = _yahoo_fundamentals_cache.get("rows")
    if (
        _yahoo_fundamentals_cache.get("key") == cache_key
        and isinstance(cached, dict)
        and float(_yahoo_fundamentals_cache.get("expires_at", 0)) > now
    ):
        return cached

    rows = await _fetch_yahoo_quote_fundamentals_uncached(settings, requested)
    _yahoo_fundamentals_cache.update(
        {
            "key": cache_key,
            "expires_at": now
            + max(settings.yahoo_fundamentals_cache_ttl_seconds, 60 * 60),
            "rows": rows,
        }
    )
    return rows


async def _fetch_yahoo_crumb(client: httpx.AsyncClient) -> str | None:
    try:
        await client.get("https://fc.yahoo.com")
        await client.get("https://finance.yahoo.com")
        response = await client.get("https://query1.finance.yahoo.com/v1/test/getcrumb")
        if response.status_code != 200:
            return None
    except httpx.HTTPError:
        return None
    crumb = response.text.strip()
    return crumb or None


def _chunks(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


async def _fetch_yahoo_quote_fundamentals_uncached(
    settings: Settings, tickers: list[str]
) -> dict[str, dict[str, Any]]:
    headers = {"User-Agent": "Mozilla/5.0"}
    rows: dict[str, dict[str, Any]] = {}

    async with httpx.AsyncClient(
        timeout=15, headers=headers, follow_redirects=True
    ) as client:
        crumb = await _fetch_yahoo_crumb(client)
        if not crumb:
            return {}

        for batch in _chunks(tickers, 50):
            try:
                response = await client.get(
                    "https://query1.finance.yahoo.com/v7/finance/quote",
                    params={"symbols": ",".join(batch), "crumb": crumb},
                )
                if response.status_code == 401:
                    crumb = await _fetch_yahoo_crumb(client)
                    if not crumb:
                        continue
                    response = await client.get(
                        "https://query1.finance.yahoo.com/v7/finance/quote",
                        params={"symbols": ",".join(batch), "crumb": crumb},
                    )
                if response.status_code != 200:
                    continue
                rows.update(normalize_yahoo_quote(response.json()))
            except (httpx.HTTPError, ValueError):
                continue

    return rows


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
        return await _with_fundamentals(settings, base_url, tickers, full_result)
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
    result = MarketDataResult(
        provider="Massive",
        status=status,
        rows=rows,
        eligible_count=len(tickers),
        loaded_count=loaded,
        detail=detail,
    )
    if result.status == "live":
        return await _with_fundamentals(settings, base_url, tickers, result)
    return result


async def _with_fundamentals(
    settings: Settings,
    base_url: str,
    tickers: list[str],
    market_result: MarketDataResult,
) -> MarketDataResult:
    fundamentals = await _fetch_fundamentals_cached(settings, base_url, tickers)
    rows: dict[str, dict[str, Any]] = {}
    fundamentals_loaded = 0
    for ticker, market in market_result.rows.items():
        merged = dict(market)
        fundamental = fundamentals.get(ticker, {})
        if fundamental:
            fundamentals_loaded += 1
            merged.update(fundamental)
            if merged.get("market_cap") is None:
                shares = merged.get("weighted_shares_outstanding")
                price = merged.get("price")
                if shares and price:
                    merged["market_cap"] = shares * price
            eps = merged.get("ttm_diluted_eps") or merged.get("ttm_basic_eps")
            if eps and merged.get("price"):
                merged["pe_ratio"] = merged["price"] / eps
        rows[ticker] = merged

    return MarketDataResult(
        provider=market_result.provider,
        status=market_result.status,
        rows=rows,
        eligible_count=market_result.eligible_count,
        loaded_count=market_result.loaded_count,
        fundamentals_loaded_count=fundamentals_loaded,
        detail=(
            f"{market_result.detail} Fundamentals populated for "
            f"{fundamentals_loaded}/{market_result.loaded_count} priced tickers."
        ),
    )


async def _fetch_fundamentals_cached(
    settings: Settings, base_url: str, tickers: list[str]
) -> dict[str, dict[str, Any]]:
    cache_key = ",".join(tickers)
    now = time.monotonic()
    cached = _fundamentals_cache.get("rows")
    if (
        _fundamentals_cache.get("key") == cache_key
        and isinstance(cached, dict)
        and float(_fundamentals_cache.get("expires_at", 0)) > now
    ):
        return cached

    rows = await _fetch_fundamentals_uncached(settings, base_url, tickers)
    _fundamentals_cache.update(
        {
            "key": cache_key,
            "expires_at": now + max(settings.massive_fundamentals_cache_ttl_seconds, 60),
            "rows": rows,
        }
    )
    return rows


async def _fetch_fundamentals_uncached(
    settings: Settings, base_url: str, tickers: list[str]
) -> dict[str, dict[str, Any]]:
    semaphore = asyncio.Semaphore(max(settings.massive_request_concurrency, 1))
    rows: dict[str, dict[str, Any]] = {}

    async with httpx.AsyncClient(base_url=base_url, timeout=15) as client:

        async def fetch_one(ticker: str) -> None:
            async with semaphore:
                overview: dict[str, Any] = {}
                financials: dict[str, Any] = {}
                try:
                    response = await client.get(
                        f"/v3/reference/tickers/{ticker}",
                        params={"apiKey": settings.massive_api_key},
                    )
                    if response.status_code == 200:
                        overview = normalize_ticker_overview(response.json())
                except (httpx.HTTPError, ValueError):
                    pass

                try:
                    response = await client.get(
                        "/vX/reference/financials",
                        params={
                            "ticker": ticker,
                            "timeframe": "ttm",
                            "limit": 1,
                            "apiKey": settings.massive_api_key,
                        },
                    )
                    if response.status_code == 200:
                        financials = normalize_financials(response.json())
                except (httpx.HTTPError, ValueError):
                    pass

                merged = {**overview, **financials}
                if merged:
                    rows[ticker] = merged

        await asyncio.gather(*(fetch_one(ticker) for ticker in tickers))

    return rows


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
        fundamentals_loaded_count=0,
        detail=detail,
    )
