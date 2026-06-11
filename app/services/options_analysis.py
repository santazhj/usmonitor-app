from __future__ import annotations

import asyncio
import copy
import math
import re
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo

import httpx

from app.config import Settings
from app.services.ibkr_options import IbkrOptionsClient, IbkrOptionsError


PRIVATE_REST_BASE_URL = "http://api.massiveprivateserver.site"


DEFAULT_OPTION_TICKERS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "TSLA",
    "AVGO",
    "ORCL",
    "AMD",
    "INTC",
    "MU",
    "ARM",
    "PLTR",
    "MRVL",
    "BE",
    "TEM",
    "AAOI",
    "LEU",
    "RKLB",
    "MSTR",
    "TSM",
    "ASML",
    "AMAT",
    "LRCX",
    "KLAC",
    "SMCI",
    "LITE",
    "COHR",
    "ANET",
    "VRT",
]

MIN_DTE = 7
MAX_DTE = 60
MAX_SCAN_DTE = 365
MIN_DELTA_ABS = 0.10
MAX_DELTA_ABS = 0.35
MAX_SPREAD_PCT = 0.12
MIN_OPEN_INTEREST = 300
CLOSED_MARKET_QUOTE_MAX_AGE_SECONDS = 84 * 60 * 60
QUOTE_STALE_SECONDS = 20 * 60
RISK_FREE_RATE = 0.045
DIVIDEND_YIELD = 0.0
DATA_SOURCES = {"massive", "ibkr"}
API_KEY_QUERY_RE = re.compile(r"(apiKey=)[^&\s)'\"\]]+")


def _effective_max_dte() -> int:
    return min(MAX_DTE, MAX_SCAN_DTE)


@dataclass
class OptionScanCacheEntry:
    payload: dict[str, Any]
    full_scanned_at: datetime


_scan_cache: dict[tuple[str, ...], OptionScanCacheEntry] = {}
_scan_cache_lock = asyncio.Lock()
_scan_progress: dict[tuple[str, ...], dict[str, Any]] = {}
_scan_progress_lock = threading.Lock()


def _normalize_base_url(value: str) -> str:
    base = (value or PRIVATE_REST_BASE_URL).strip().rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = f"https://{base}"
    return base


def _normalize_data_source(settings: Settings, value: str | None = None) -> str:
    source = (value or settings.option_data_source or "massive").strip().lower()
    if source not in DATA_SOURCES:
        raise RuntimeError(f"Unsupported option data source: {source}. Choose massive or ibkr.")
    return source


def _cache_key(source: str, tickers: list[str]) -> tuple[str, ...]:
    return (source, *tickers)


def _start_progress(key: tuple[str, ...], source: str, tickers: list[str], mode: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _scan_progress_lock:
        _scan_progress[key] = {
            "active": True,
            "source": source,
            "mode": mode,
            "tickers": tickers,
            "total": len(tickers),
            "completed": 0,
            "stage": "queued",
            "currentTicker": None,
            "message": f"Queued {len(tickers)} tickers",
            "contracts": 0,
            "quoteRequests": 0,
            "quotesWithBidAsk": 0,
            "quotesWithGreeks": 0,
            "errors": [],
            "events": [],
            "startedAt": now,
            "updatedAt": now,
            "finishedAt": None,
        }


def _update_progress(key: tuple[str, ...], event: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _scan_progress_lock:
        current = _scan_progress.setdefault(key, {"active": True, "events": [], "errors": [], "startedAt": now})
        ticker = event.get("ticker")
        stage = event.get("stage")
        message = event.get("message")
        if ticker:
            current["currentTicker"] = ticker
        if stage:
            current["stage"] = stage
        if message:
            current["message"] = message
        for field in ("total", "completed", "contracts", "quoteRequests", "quotesWithBidAsk", "quotesWithGreeks"):
            if field in event:
                current[field] = event[field]
        if stage == "error" and message:
            errors = list(current.get("errors") or [])
            errors.append(message)
            current["errors"] = errors[-8:]
        events = list(current.get("events") or [])
        if stage or message:
            events.append({"time": now, "ticker": ticker, "stage": stage, "message": message})
            current["events"] = events[-10:]
        current["updatedAt"] = now


def _finish_progress(key: tuple[str, ...], success: bool, message: str, contracts: int = 0) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _scan_progress_lock:
        current = _scan_progress.setdefault(key, {"events": [], "errors": [], "startedAt": now})
        current["active"] = False
        current["success"] = success
        current["stage"] = "done" if success else "failed"
        current["message"] = message
        current["contracts"] = contracts
        current["updatedAt"] = now
        current["finishedAt"] = now


def options_progress_snapshot(settings: Settings, raw_tickers: str | list[str] | None = None, source: str | None = None) -> dict[str, Any]:
    tickers = normalize_tickers(raw_tickers)
    normalized_source = _normalize_data_source(settings, source)
    key = _cache_key(normalized_source, tickers)
    with _scan_progress_lock:
        progress = copy.deepcopy(_scan_progress.get(key))
    if progress:
        return progress
    return {
        "active": False,
        "source": normalized_source,
        "tickers": tickers,
        "total": len(tickers),
        "completed": 0,
        "stage": "idle",
        "currentTicker": None,
        "message": "Idle",
        "contracts": 0,
        "quoteRequests": 0,
        "quotesWithBidAsk": 0,
        "quotesWithGreeks": 0,
        "errors": [],
        "events": [],
    }


def _current_us_market_date(now: datetime | None = None) -> date:
    current = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo("America/New_York")).date()
    if current.weekday() == 5:
        return date.fromordinal(current.toordinal() - 1)
    if current.weekday() == 6:
        return date.fromordinal(current.toordinal() - 2)
    return current


def _with_api_key(url: str, api_key: str, base_url: str) -> str:
    parsed = urlparse(url)
    base = urlparse(base_url)
    if base.netloc and parsed.netloc and parsed.netloc != base.netloc:
        parsed = parsed._replace(scheme=base.scheme, netloc=base.netloc)
    query = parse_qs(parsed.query)
    query.setdefault("apiKey", [api_key])
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def _redact_api_key(value: Any) -> str:
    return API_KEY_QUERY_RE.sub(r"\1<redacted>", str(value))


async def _get_json(
    client: httpx.AsyncClient,
    settings: Settings,
    path_or_url: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not settings.massive_api_key:
        raise RuntimeError("MASSIVE_API_KEY is not configured.")

    base_url = _normalize_base_url(settings.massive_base_url)
    request_params = dict(params or {})
    if path_or_url.startswith("http"):
        parsed = urlparse(path_or_url)
        base = urlparse(base_url)
        if parsed.netloc == base.netloc and "apiKey=" in parsed.query:
            url = path_or_url
        else:
            url = _with_api_key(path_or_url, settings.massive_api_key, base_url)
        request_params = None
    else:
        url = f"{base_url}{path_or_url}"
        request_params["apiKey"] = settings.massive_api_key

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await client.get(url, params=request_params, timeout=45)
            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                try:
                    wait_seconds = float(retry_after) if retry_after else 8.0
                except ValueError:
                    wait_seconds = 8.0
                await asyncio.sleep(max(2.0, min(wait_seconds, 30.0)))
                continue
            response.raise_for_status()
            payload = response.json()
            status = str(payload.get("status", "")).lower()
            if status and status not in {"ok", "success", "delayed"}:
                raise RuntimeError(f"Massive status={payload.get('status')}: {payload}")
            return payload
        except Exception as exc:  # noqa: BLE001
            last_error = RuntimeError(_redact_api_key(exc))
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Massive request failed: {_redact_api_key(last_error)}")


async def _paged_results(
    client: httpx.AsyncClient,
    settings: Settings,
    path: str,
    params: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    payload = await _get_json(client, settings, path, params)
    results.extend(payload.get("results") or [])
    next_url = payload.get("next_url")
    while next_url:
        next_url = _with_api_key(
            str(next_url),
            settings.massive_api_key,
            _normalize_base_url(settings.massive_base_url),
        )
        payload = await _get_json(client, settings, next_url)
        results.extend(payload.get("results") or [])
        next_url = payload.get("next_url")
    return results


def _pick(mapping: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if mapping.get(key) is not None:
            return mapping[key]
    return default


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _timestamp_to_datetime(value: Any) -> datetime | None:
    numeric = _to_float(value)
    if numeric is None or numeric <= 0:
        return None
    if numeric > 10_000_000_000_000_000:
        seconds = numeric / 1_000_000_000
    elif numeric > 10_000_000_000:
        seconds = numeric / 1000
    else:
        seconds = numeric
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def _annualized_yield(credit: float, strike: float, dte: int) -> float:
    if credit <= 0 or strike <= 0 or dte <= 0:
        return 0.0
    return credit / strike * 365 / dte


def _cycle_put_edge_ratio(expiry_yield: float, delta_abs: float | None, buffer_em_ratio: float | None) -> float:
    if expiry_yield <= 0 or delta_abs is None or delta_abs <= 0:
        return 0.0
    if buffer_em_ratio is None or buffer_em_ratio <= 0:
        return 0.0
    return max(0.0, expiry_yield / delta_abs * min(buffer_em_ratio, 2.0))


def _dte_bucket(dte: int) -> str:
    if dte <= 14:
        return "07-14D"
    if dte <= 30:
        return "15-30D"
    if dte <= 45:
        return "31-45D"
    if dte <= 75:
        return "46-75D"
    if dte <= 120:
        return "76-120D"
    return "121-365D"


def _dte_bucket_preference(bucket: str) -> float:
    return {
        "07-14D": 0.25,
        "15-30D": 0.65,
        "31-45D": 1.00,
        "46-75D": 0.92,
        "76-120D": 0.62,
        "121-365D": 0.42,
    }.get(bucket, 0.50)


def _monthly_score(record: dict[str, Any]) -> float:
    if not record.get("platform_valid", True):
        return 0.0
    bucket_rank = _to_float(record.get("bucket_rank") or record.get("put_edge_rank"), 0.0) or 0.0
    quality = max(0.0, min(1.0, (_to_float(record.get("score"), 0.0) or 0.0) / 100.0))
    bucket_preference = _dte_bucket_preference(str(record.get("dte_bucket") or ""))
    return round(100.0 * (0.55 * bucket_rank + 0.25 * quality + 0.20 * bucket_preference), 2)


def _expected_move(spot: float, iv: float | None, dte: int) -> float | None:
    if not iv or iv <= 0 or spot <= 0 or dte <= 0:
        return None
    return spot * iv * math.sqrt(dte / 365)


def _liquidity_factor(spread_pct: float, open_interest: int) -> float:
    spread_score = max(0.0, min(1.0, 1 - spread_pct / MAX_SPREAD_PCT))
    oi_score = max(0.0, min(1.0, open_interest / (MIN_OPEN_INTEREST * 4)))
    return 0.55 * spread_score + 0.45 * oi_score


def _freshness_factor(quote_age_seconds: float | None, closed_reference: bool) -> float:
    if closed_reference:
        return 1.0
    if quote_age_seconds is None:
        return 0.0
    return max(0.0, min(1.0, 1 - quote_age_seconds / QUOTE_STALE_SECONDS))


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def _black_scholes_put_price(
    spot: float,
    strike: float,
    dte: int,
    iv: float | None,
) -> float | None:
    if spot <= 0 or strike <= 0 or dte <= 0 or not iv or iv <= 0:
        return None
    t = dte / 365
    sigma_sqrt_t = iv * math.sqrt(t)
    if sigma_sqrt_t <= 0:
        return None
    d1 = (
        math.log(spot / strike)
        + (RISK_FREE_RATE - DIVIDEND_YIELD + 0.5 * iv * iv) * t
    ) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return strike * math.exp(-RISK_FREE_RATE * t) * _normal_cdf(-d2) - spot * math.exp(
        -DIVIDEND_YIELD * t
    ) * _normal_cdf(-d1)


def _edge_flag(flags: list[str], cycle_ratio: float, bucket_rank: float = 0.0, monthly_score: float = 0.0) -> str:
    if "stale_quote" in flags:
        return "Stale"
    if "invalid_quote" in flags or "missing_delta" in flags or "missing_iv" in flags:
        return "Data Gap"
    if "wide_spread" in flags or "low_open_interest" in flags:
        return "Liquidity"
    if monthly_score >= 80 or (cycle_ratio >= 0.12 and bucket_rank >= 0.95):
        return "Extreme"
    if monthly_score >= 68 or (cycle_ratio >= 0.08 and bucket_rank >= 0.85):
        return "Good"
    if monthly_score >= 55 or cycle_ratio >= 0.05:
        return "Watch"
    return "Normal"


def _stress(spot: float, strike: float, credit: float, expected_move: float | None) -> dict[str, float]:
    scenarios = {
        "stress_down_10pct": spot * 0.90,
        "stress_down_20pct": spot * 0.80,
        "stress_down_30pct": spot * 0.70,
    }
    if expected_move:
        scenarios["stress_1sigma"] = spot - expected_move
        scenarios["stress_2sigma"] = spot - expected_move * 2
    return {
        key: round((credit - max(0.0, strike - scenario_price)) * 100, 2)
        for key, scenario_price in scenarios.items()
    }


def _market_valid(flags: list[str]) -> bool:
    hard_flags = {
        "non_standard_contract",
        "not_otm",
        "invalid_quote",
        "wide_spread",
        "low_open_interest",
        "missing_delta",
        "delta_out_of_range",
        "missing_iv",
        "missing_quote_time",
        "stale_quote",
    }
    return not any(flag in hard_flags for flag in flags)


def _option_record(
    raw: dict[str, Any],
    now: datetime | None = None,
    underlying_ticker: str = "",
) -> dict[str, Any] | None:
    now = now or datetime.now(timezone.utc)
    today = _current_us_market_date(now)
    details = raw.get("details") or {}
    quote = raw.get("last_quote") or {}
    greeks = raw.get("greeks") or {}
    underlying = raw.get("underlying_asset") or {}

    try:
        expiry = date.fromisoformat(str(_pick(details, ("expiration_date",))))
        strike = float(_pick(details, ("strike_price",)))
    except (TypeError, ValueError):
        return None

    ticker = str(_pick(details, ("underlying_ticker",), underlying_ticker)).upper()
    option_ticker = str(_pick(details, ("ticker",), ""))
    dte = (expiry - today).days
    spot = _to_float(_pick(underlying, ("price", "last", "close", "value")), 0.0) or 0.0
    if not spot:
        spot = _to_float(_pick(raw.get("day") or {}, ("c", "close")), 0.0) or 0.0

    bid = _to_float(_pick(quote, ("bid", "bid_price", "bp")), 0.0) or 0.0
    ask = _to_float(_pick(quote, ("ask", "ask_price", "ap")), 0.0) or 0.0
    bid_size = _to_int(_pick(quote, ("bid_size", "bs")), 0)
    ask_size = _to_int(_pick(quote, ("ask_size", "as")), 0)
    mid = (bid + ask) / 2 if bid > 0 and ask > 0 else 0.0
    target_credit = bid + max(0.0, ask - bid) * 0.25 if bid > 0 and ask > bid else bid
    spread_pct = (ask - bid) / mid if mid > 0 else 1.0
    delta = _to_float(_pick(greeks, ("delta",)))
    gamma = _to_float(_pick(greeks, ("gamma",)))
    vega = _to_float(_pick(greeks, ("vega",)))
    theta = _to_float(_pick(greeks, ("theta",)))
    rho = _to_float(_pick(greeks, ("rho",)))
    iv = _to_float(raw.get("implied_volatility"))
    open_interest = _to_int(raw.get("open_interest"), 0)
    shares_per_contract = _to_int(_pick(details, ("shares_per_contract",), 100), 100)
    quote_time = _timestamp_to_datetime(
        _pick(quote, ("last_updated", "sip_timestamp", "t", "timestamp"))
    )
    quote_age_seconds = (now - quote_time).total_seconds() if quote_time else None
    closed_reference = bool(
        quote_age_seconds is not None
        and QUOTE_STALE_SECONDS < quote_age_seconds <= CLOSED_MARKET_QUOTE_MAX_AGE_SECONDS
    )
    quote_mode = "Close Ref" if closed_reference else "Live"

    breakeven = strike - target_credit
    breakeven_buffer = (spot - breakeven) / spot if spot > 0 else 0.0
    expected_move = _expected_move(spot, iv, dte)
    buffer_em_ratio = (
        (spot - breakeven) / expected_move if expected_move and expected_move > 0 else None
    )
    ann_yield_bid = _annualized_yield(bid, strike, dte)
    ann_yield_mid = _annualized_yield(mid, strike, dte)
    liquidity = _liquidity_factor(spread_pct, open_interest)
    freshness = _freshness_factor(quote_age_seconds, closed_reference)
    delta_abs = abs(delta) if delta is not None else None
    expiry_yield = target_credit / strike if strike > 0 else None
    cycle_edge = _cycle_put_edge_ratio(expiry_yield or 0.0, delta_abs, buffer_em_ratio)
    put_edge_ratio = (
        ann_yield_bid
        / max(delta_abs or 0, 0.01)
        * min(max(buffer_em_ratio or 0, 0), 2.0)
    )
    bs_price = _black_scholes_put_price(spot, strike, dte, iv)
    premium_vs_bs = target_credit / bs_price - 1 if bs_price and bs_price > 0 else None

    flags: list[str] = []
    if details.get("contract_type") != "put":
        flags.append("not_put")
    if shares_per_contract != 100:
        flags.append("non_standard_contract")
    if not (MIN_DTE <= dte <= _effective_max_dte()):
        flags.append("dte_out_of_range")
    if strike >= spot:
        flags.append("not_otm")
    if bid <= 0 or ask <= 0 or ask < bid:
        flags.append("invalid_quote")
    if spread_pct > MAX_SPREAD_PCT:
        flags.append("wide_spread")
    if open_interest < MIN_OPEN_INTEREST:
        flags.append("low_open_interest")
    if delta is None:
        flags.append("missing_delta")
    elif not (MIN_DELTA_ABS <= abs(delta) <= MAX_DELTA_ABS):
        flags.append("delta_out_of_range")
    if iv is None:
        flags.append("missing_iv")
    if quote_time is None:
        flags.append("missing_quote_time")
    elif quote_age_seconds and quote_age_seconds > QUOTE_STALE_SECONDS and not closed_reference:
        flags.append("stale_quote")
    if closed_reference:
        flags.append("closed_market_reference")
    if ann_yield_mid > 0.30:
        flags.append("high_annualized_yield")
    if breakeven_buffer < 0.05:
        flags.append("thin_breakeven_buffer")

    return {
        "ticker": ticker,
        "option_ticker": option_ticker,
        "topContract": f"{expiry.isoformat()} P{strike:.2f}",
        "expiry": expiry.isoformat(),
        "strike": strike,
        "dte": dte,
        "spot": spot,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "bid_size": bid_size,
        "ask_size": ask_size,
        "target_credit": target_credit,
        "expiry_yield": expiry_yield,
        "ann_yield_bid": ann_yield_bid,
        "ann_yield_mid": ann_yield_mid,
        "delta": delta,
        "gamma": gamma,
        "vega": vega,
        "theta": theta,
        "rho": rho,
        "iv": iv,
        "open_interest": open_interest,
        "spread_pct": spread_pct,
        "breakeven": breakeven,
        "breakeven_buffer": breakeven_buffer,
        "expected_move": expected_move,
        "buffer_em_ratio": buffer_em_ratio,
        "put_edge_ratio": put_edge_ratio,
        "cycle_put_edge_ratio": cycle_edge,
        "dte_bucket": _dte_bucket(dte),
        "bs_put_price": bs_price,
        "premium_vs_bs_pct": premium_vs_bs,
        "quote_time": quote_time.isoformat() if quote_time else None,
        "quote_age_seconds": quote_age_seconds,
        "quote_mode": quote_mode,
        "platform_valid": _market_valid(flags),
        "edge_flag": _edge_flag(flags, cycle_edge),
        "score": min(100.0, max(0.0, put_edge_ratio * 35 + breakeven_buffer * 220 + liquidity * 20)),
        "risk_flags": ", ".join(flags),
        **_stress(spot, strike, target_credit, expected_move),
    }


def _median(values: list[Any]) -> float | None:
    numeric = sorted(value for value in (_to_float(item) for item in values) if value is not None)
    if not numeric:
        return None
    mid = len(numeric) // 2
    if len(numeric) % 2:
        return numeric[mid]
    return (numeric[mid - 1] + numeric[mid]) / 2


def _add_bucket_rankings(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_bucket: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        record["dte_bucket"] = record.get("dte_bucket") or _dte_bucket(_to_int(record.get("dte"), 0))
        by_bucket.setdefault(str(record["dte_bucket"]), []).append(record)

    for bucket_records in by_bucket.values():
        rankable = [item for item in bucket_records if item.get("platform_valid")]
        for record in bucket_records:
            record["bucket_rank"] = 0.0
            record["put_edge_rank"] = 0.0
            record["monthly_score"] = 0.0
        values = sorted(_to_float(item.get("cycle_put_edge_ratio"), 0.0) or 0.0 for item in rankable)
        total = len(values)
        if total <= 0:
            for record in bucket_records:
                flags = str(record.get("risk_flags") or "").split(", ")
                record["edge_flag"] = _edge_flag(flags, _to_float(record.get("cycle_put_edge_ratio"), 0.0) or 0.0)
            continue
        for record in rankable:
            value = _to_float(record.get("cycle_put_edge_ratio"), 0.0) or 0.0
            rank = sum(1 for item in values if item <= value) / total
            record["bucket_rank"] = rank
            record["put_edge_rank"] = rank
            record["monthly_score"] = _monthly_score(record)
            flags = str(record.get("risk_flags") or "").split(", ")
            record["edge_flag"] = _edge_flag(flags, value, rank, record["monthly_score"])
    return records


def _summarize(records: list[dict[str, Any]], underlyings: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [item for item in records if item.get("platform_valid")]
    now = datetime.now(timezone.utc).isoformat()
    return {
        "underlyings": len(underlyings),
        "contracts": len(records),
        "validContracts": len(valid),
        "analyzableContractRate": len(valid) / len(records) if records else 0,
        "validQuoteRate": len(valid) / len(records) if records else 0,
        "bestPer": max((_to_float(item.get("put_edge_ratio"), 0.0) or 0.0 for item in valid), default=None),
        "bestCyclePer": max((_to_float(item.get("cycle_put_edge_ratio"), 0.0) or 0.0 for item in valid), default=None),
        "bestMonthlyScore": max((_to_float(item.get("monthly_score"), 0.0) or 0.0 for item in valid), default=None),
        "medianIv": _median([item.get("iv") for item in valid]),
        "medianSpread": _median([item.get("spread_pct") for item in valid]),
        "medianBuffer": _median([item.get("breakeven_buffer") for item in valid]),
        "lastRefresh": now,
        "fullScanAt": now,
        "refreshMode": "full",
        "quickContractsRefreshed": 0,
    }


def _top_options(records: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
    valid = [item for item in records if item.get("platform_valid")]
    selected = valid or records
    return sorted(
        selected,
        key=lambda item: (
            _to_float(item.get("monthly_score"), 0.0) or 0.0,
            _to_float(item.get("bucket_rank"), 0.0) or 0.0,
            _to_float(item.get("cycle_put_edge_ratio"), 0.0) or 0.0,
            _to_float(item.get("score"), 0.0) or 0.0,
            _to_float(item.get("put_edge_ratio"), 0.0) or 0.0,
        ),
        reverse=True,
    )[:limit]


def _payload_from_records(
    tickers: list[str],
    records: list[dict[str, Any]],
    errors: list[str],
    source: str = "massive",
) -> dict[str, Any]:
    records = _add_bucket_rankings(records)
    underlyings: list[dict[str, Any]] = []
    by_ticker: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_ticker.setdefault(str(record.get("ticker") or ""), []).append(record)
    for ticker in tickers:
        group = by_ticker.get(ticker, [])
        if not group:
            continue
        top = _top_options(group)
        if not top:
            continue
        best = dict(top[0])
        best["topOptions"] = top
        best["contractsScanned"] = len(group)
        best["validContracts"] = len([item for item in group if item.get("platform_valid")])
        underlyings.append(best)

    underlyings.sort(
        key=lambda item: (
            _to_float(item.get("monthly_score"), 0.0) or 0.0,
            _to_float(item.get("bucket_rank"), 0.0) or 0.0,
            _to_float(item.get("cycle_put_edge_ratio"), 0.0) or 0.0,
            _to_float(item.get("score"), 0.0) or 0.0,
        ),
        reverse=True,
    )
    return {
        "summary": {**_summarize(records, underlyings), "dataSource": source},
        "underlyings": underlyings,
        "errors": errors,
        "tickers": tickers,
    }


def normalize_tickers(raw_tickers: str | list[str] | None) -> list[str]:
    if isinstance(raw_tickers, str):
        items = raw_tickers.split(",")
    else:
        items = raw_tickers or DEFAULT_OPTION_TICKERS
    tickers = [str(item).strip().upper() for item in items if str(item).strip()]
    return list(dict.fromkeys(tickers))


async def build_massive_full_payload(
    settings: Settings,
    tickers: list[str],
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    today = _current_us_market_date()
    max_dte = _effective_max_dte()
    params = {
        "contract_type": "put",
        "expiration_date.gte": date.fromordinal(today.toordinal() + MIN_DTE).isoformat(),
        "expiration_date.lte": date.fromordinal(today.toordinal() + max_dte).isoformat(),
        "limit": 250,
        "sort": "expiration_date",
        "order": "asc",
    }
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    semaphore = asyncio.Semaphore(max(1, min(settings.massive_request_concurrency, 6)))
    completed = 0
    completed_lock = asyncio.Lock()
    progress = progress_callback or (lambda event: None)

    async with httpx.AsyncClient() as client:
        async def scan_ticker(ticker: str) -> None:
            nonlocal completed
            async with semaphore:
                progress({"stage": "option_chain", "ticker": ticker, "message": f"{ticker}: loading Massive option chain", "total": len(tickers), "completed": completed})
                try:
                    raw_chain = await _paged_results(
                        client,
                        settings,
                        f"/v3/snapshot/options/{ticker}",
                        params,
                    )
                except Exception as exc:  # noqa: BLE001
                    error = f"{ticker}: {_redact_api_key(exc)}"
                    errors.append(error)
                    async with completed_lock:
                        completed += 1
                        progress({"stage": "error", "ticker": ticker, "message": error, "total": len(tickers), "completed": completed, "contracts": len(records)})
                    return
                ticker_records = []
                for raw in raw_chain:
                    record = _option_record(raw, underlying_ticker=ticker)
                    if record:
                        ticker_records.append(record)
                records.extend(ticker_records)
                async with completed_lock:
                    completed += 1
                    progress({"stage": "ticker_done", "ticker": ticker, "message": f"{ticker}: {len(ticker_records)} contracts", "total": len(tickers), "completed": completed, "contracts": len(records)})

        await asyncio.gather(*(scan_ticker(ticker) for ticker in tickers))

    progress({"stage": "done", "message": "Scan complete" if not errors else f"Scan complete with {len(errors)} errors", "total": len(tickers), "completed": len(tickers), "contracts": len(records)})
    payload = _payload_from_records(tickers, records, errors, source="massive")
    key = _cache_key("massive", tickers)
    async with _scan_cache_lock:
        _scan_cache[key] = OptionScanCacheEntry(
            payload=copy.deepcopy(payload),
            full_scanned_at=datetime.now(timezone.utc),
        )
    return payload


def _build_ibkr_full_payload_sync(
    settings: Settings,
    tickers: list[str],
    progress_callback: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    today = _current_us_market_date()
    min_expiry = date.fromordinal(today.toordinal() + MIN_DTE).isoformat()
    max_expiry = date.fromordinal(today.toordinal() + _effective_max_dte()).isoformat()
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    client = IbkrOptionsClient(
        host=settings.ibkr_host,
        port=settings.ibkr_port,
        client_id=settings.ibkr_client_id,
        timeout_seconds=settings.ibkr_timeout_seconds,
        market_data_type=settings.ibkr_market_data_type,
        max_option_quotes=settings.ibkr_max_option_quotes,
        snapshot_timeout_seconds=settings.ibkr_snapshot_timeout_seconds,
        progress_callback=progress_callback,
    )
    try:
        progress_callback({"stage": "start", "message": f"Scanning {len(tickers)} tickers", "total": len(tickers), "completed": 0})
        for idx, ticker in enumerate(tickers, start=1):
            progress_callback({"stage": "option_chain", "ticker": ticker, "message": f"{ticker}: loading option chain", "total": len(tickers), "completed": idx - 1})
            try:
                raw_chain = client.get_option_chain(ticker, expiration_date_gte=min_expiry, expiration_date_lte=max_expiry)
            except IbkrOptionsError as exc:
                error = f"{ticker} option chain: {exc}"
                errors.append(error)
                progress_callback({"stage": "error", "ticker": ticker, "message": error, "total": len(tickers), "completed": idx})
                continue
            progress_callback({"stage": "scoring", "ticker": ticker, "message": f"{ticker}: scoring {len(raw_chain)} contracts", "contracts": len(raw_chain), "total": len(tickers), "completed": idx - 1})
            for raw in raw_chain:
                record = _option_record(raw, underlying_ticker=ticker)
                if record:
                    records.append(record)
            progress_callback({"stage": "ticker_done", "ticker": ticker, "message": f"{ticker}: done", "contracts": len(raw_chain), "total": len(tickers), "completed": idx})
        progress_callback({"stage": "done", "message": "Scan complete", "total": len(tickers), "completed": len(tickers), "contracts": len(records)})
        return _payload_from_records(tickers, records, errors, source="ibkr")
    finally:
        client.disconnect()


async def build_ibkr_full_payload(
    settings: Settings,
    tickers: list[str],
    progress_callback: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    payload = await asyncio.to_thread(_build_ibkr_full_payload_sync, settings, tickers, progress_callback)
    key = _cache_key("ibkr", tickers)
    async with _scan_cache_lock:
        _scan_cache[key] = OptionScanCacheEntry(
            payload=copy.deepcopy(payload),
            full_scanned_at=datetime.now(timezone.utc),
        )
    return payload


async def build_full_payload(settings: Settings, tickers: list[str], source: str = "massive") -> dict[str, Any]:
    normalized_source = _normalize_data_source(settings, source)
    key = _cache_key(normalized_source, tickers)
    _start_progress(key, normalized_source, tickers, mode="full")
    progress_callback = lambda event: _update_progress(key, event)
    try:
        payload = (
            await build_ibkr_full_payload(settings, tickers, progress_callback)
            if normalized_source == "ibkr"
            else await build_massive_full_payload(settings, tickers, progress_callback)
        )
        contracts = int(payload.get("summary", {}).get("contracts") or 0)
        errors = list(payload.get("errors") or [])
        success = not (errors and contracts == 0)
        message = "Scan complete" if not errors else f"Scan complete with {len(errors)} errors"
        if not success:
            message = errors[0] if len(errors) == 1 else f"Scan failed for {len(errors)} tickers"
        _finish_progress(key, success=success, message=message, contracts=contracts)
        return payload
    except Exception as exc:  # noqa: BLE001
        _update_progress(key, {"stage": "error", "message": str(exc)})
        _finish_progress(key, success=False, message=str(exc))
        raise


def _quick_no_cache_payload(tickers: list[str], source: str = "massive") -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "summary": {
            "dataSource": source,
            "underlyings": len(tickers),
            "contracts": 0,
            "validContracts": 0,
            "analyzableContractRate": 0.0,
            "validQuoteRate": 0.0,
            "bestPer": None,
            "bestCyclePer": None,
            "bestMonthlyScore": None,
            "medianIv": None,
            "medianSpread": None,
            "medianBuffer": None,
            "lastRefresh": now,
            "refreshMode": "quick_no_cache",
            "quickContractsRefreshed": 0,
            "fullScanRequired": True,
        },
        "underlyings": [],
        "errors": [],
        "tickers": tickers,
    }


def _quote_has_bid_ask(record: dict[str, Any]) -> bool:
    return (_to_float(record.get("bid"), 0.0) or 0.0) > 0 and (_to_float(record.get("ask"), 0.0) or 0.0) > 0


def _quote_has_greeks(record: dict[str, Any]) -> bool:
    return record.get("delta") is not None and record.get("iv") is not None


async def _refresh_best_option(
    client: httpx.AsyncClient,
    settings: Settings,
    row: dict[str, Any],
) -> dict[str, Any]:
    ticker = str(row.get("ticker") or "").upper()
    option_ticker = str(row.get("option_ticker") or "")
    if not ticker or not option_ticker:
        return row
    raw = await _get_json(client, settings, f"/v3/snapshot/options/{ticker}/{option_ticker}")
    refreshed = _option_record(raw.get("results") or raw, underlying_ticker=ticker)
    if not refreshed:
        return row
    refreshed["bucket_rank"] = row.get("bucket_rank")
    refreshed["put_edge_rank"] = row.get("put_edge_rank")
    refreshed["monthly_score"] = row.get("monthly_score")
    refreshed["dte_bucket"] = row.get("dte_bucket") or refreshed.get("dte_bucket")
    if not refreshed.get("platform_valid"):
        refreshed["bucket_rank"] = 0.0
        refreshed["put_edge_rank"] = 0.0
        refreshed["monthly_score"] = 0.0
    refreshed["contractsScanned"] = row.get("contractsScanned")
    refreshed["validContracts"] = row.get("validContracts")
    top_options = list(row.get("topOptions") or [])
    for idx, option in enumerate(top_options):
        if option.get("option_ticker") == option_ticker:
            top_options[idx] = {**option, **refreshed}
            break
    else:
        top_options.insert(0, refreshed)
    refreshed["topOptions"] = top_options[:10]
    return refreshed


async def build_quick_payload(
    settings: Settings,
    tickers: list[str],
    source: str = "massive",
    allow_initial_full: bool = False,
) -> dict[str, Any]:
    normalized_source = _normalize_data_source(settings, source)
    key = _cache_key(normalized_source, tickers)
    async with _scan_cache_lock:
        entry = _scan_cache.get(key)
        cached = copy.deepcopy(entry.payload) if entry else None
        full_scanned_at = entry.full_scanned_at if entry else None
    if cached is None and allow_initial_full:
        payload = await build_full_payload(settings, tickers, source=normalized_source)
        payload["summary"]["refreshMode"] = "full_initial"
        return payload
    if cached is None:
        _start_progress(key, normalized_source, tickers, mode="quick")
        _update_progress(
            key,
            {
                "stage": "no_cache",
                "message": "Quick refresh needs one full scan first",
                "total": 0,
                "completed": 0,
                "contracts": 0,
                "quoteRequests": 0,
                "quotesWithBidAsk": 0,
                "quotesWithGreeks": 0,
            },
        )
        _finish_progress(key, success=True, message="Run full scan first", contracts=0)
        return _quick_no_cache_payload(tickers, source=normalized_source)

    rows_to_refresh = list(cached.get("underlyings") or [])
    summary_before = dict(cached.get("summary") or {})
    total_rows = len(rows_to_refresh)
    total_contracts = int(summary_before.get("contracts") or sum(int(row.get("contractsScanned") or 0) for row in rows_to_refresh))
    _start_progress(key, normalized_source, tickers, mode="quick")
    _update_progress(
        key,
        {
            "stage": "quick_refresh",
            "message": f"Refreshing {total_rows} cached option quotes",
            "total": total_rows,
            "completed": 0,
            "contracts": total_contracts,
            "quoteRequests": 0,
            "quotesWithBidAsk": 0,
            "quotesWithGreeks": 0,
        },
    )

    if normalized_source == "ibkr":
        now = datetime.now(timezone.utc)
        summary = dict(cached.get("summary") or {})
        summary["dataSource"] = normalized_source
        summary["lastRefresh"] = now.isoformat()
        summary["quickRefreshAt"] = now.isoformat()
        summary["fullScanAt"] = full_scanned_at.isoformat() if full_scanned_at else summary.get("fullScanAt")
        summary["fullScanAgeSeconds"] = int((now - full_scanned_at).total_seconds()) if full_scanned_at else None
        summary["quickContractsRefreshed"] = 0
        summary["refreshMode"] = "quick_cached"
        cached["summary"] = summary
        _update_progress(
            key,
            {
                "stage": "quick_cached",
                "message": "IBKR quick refresh uses the latest full-scan cache",
                "total": total_rows,
                "completed": total_rows,
                "contracts": total_contracts,
                "quoteRequests": 0,
                "quotesWithBidAsk": 0,
                "quotesWithGreeks": 0,
            },
        )
        _finish_progress(key, success=True, message="Quick refresh used cached IBKR scan", contracts=total_contracts)
        return cached

    errors = list(cached.get("errors") or [])
    refreshed_count = 0
    bid_ask_count = 0
    greeks_count = 0
    async with httpx.AsyncClient() as client:
        for idx, row in enumerate(rows_to_refresh, start=1):
            ticker = str(row.get("ticker") or "").upper()
            option_ticker = str(row.get("option_ticker") or "")
            _update_progress(
                key,
                {
                    "stage": "quote_refresh",
                    "ticker": ticker,
                    "message": f"{ticker}: refreshing {option_ticker or 'best contract'}",
                    "total": total_rows,
                    "completed": idx - 1,
                    "contracts": total_contracts,
                    "quoteRequests": idx - 1,
                    "quotesWithBidAsk": bid_ask_count,
                    "quotesWithGreeks": greeks_count,
                },
            )
            try:
                refreshed = await _refresh_best_option(client, settings, row)
            except Exception as exc:  # noqa: BLE001
                error = f"{row.get('ticker')} quick refresh: {exc}"
                errors.append(error)
                _update_progress(
                    key,
                    {
                        "stage": "error",
                        "ticker": ticker,
                        "message": error,
                        "total": total_rows,
                        "completed": idx,
                        "contracts": total_contracts,
                        "quoteRequests": idx,
                        "quotesWithBidAsk": bid_ask_count,
                        "quotesWithGreeks": greeks_count,
                    },
                )
                continue
            row.update(refreshed)
            refreshed_count += 1
            if _quote_has_bid_ask(refreshed):
                bid_ask_count += 1
            if _quote_has_greeks(refreshed):
                greeks_count += 1
            bid = _to_float(refreshed.get("bid"), 0.0) or 0.0
            ask = _to_float(refreshed.get("ask"), 0.0) or 0.0
            quote_message = f"{ticker}: {bid:.2f} / {ask:.2f}" if bid and ask else f"{ticker}: no valid bid/ask"
            _update_progress(
                key,
                {
                    "stage": "ticker_done",
                    "ticker": ticker,
                    "message": quote_message,
                    "total": total_rows,
                    "completed": idx,
                    "contracts": total_contracts,
                    "quoteRequests": idx,
                    "quotesWithBidAsk": bid_ask_count,
                    "quotesWithGreeks": greeks_count,
                },
            )

    cached["underlyings"].sort(
        key=lambda item: (
            _to_float(item.get("put_edge_ratio"), 0.0) or 0.0,
            _to_float(item.get("score"), 0.0) or 0.0,
        ),
        reverse=True,
    )
    summary = dict(cached.get("summary") or {})
    now = datetime.now(timezone.utc)
    summary["lastRefresh"] = now.isoformat()
    summary["quickRefreshAt"] = now.isoformat()
    summary["fullScanAt"] = full_scanned_at.isoformat() if full_scanned_at else summary.get("fullScanAt")
    summary["fullScanAgeSeconds"] = int((now - full_scanned_at).total_seconds()) if full_scanned_at else None
    summary["quickContractsRefreshed"] = refreshed_count
    summary["refreshMode"] = "quick"
    source_rows = [row for row in cached["underlyings"] if row.get("platform_valid")]
    summary["bestPer"] = max((_to_float(row.get("put_edge_ratio"), 0.0) or 0.0 for row in source_rows), default=None)
    summary["bestCyclePer"] = max((_to_float(row.get("cycle_put_edge_ratio"), 0.0) or 0.0 for row in source_rows), default=None)
    summary["bestMonthlyScore"] = max((_to_float(row.get("monthly_score"), 0.0) or 0.0 for row in source_rows), default=None)
    summary["medianIv"] = _median([row.get("iv") for row in source_rows])
    summary["medianSpread"] = _median([row.get("spread_pct") for row in source_rows])
    summary["medianBuffer"] = _median([row.get("breakeven_buffer") for row in source_rows])
    cached["summary"] = summary
    cached["errors"] = errors
    async with _scan_cache_lock:
        _scan_cache[key] = OptionScanCacheEntry(
            payload=copy.deepcopy(cached),
            full_scanned_at=full_scanned_at or now,
        )
    message = f"Quick refresh complete: {refreshed_count}/{total_rows} quotes"
    if errors:
        message = f"{message}, {len(errors)} errors"
    _finish_progress(key, success=True, message=message, contracts=total_contracts)
    return cached


async def build_options_payload(
    settings: Settings,
    raw_tickers: str | list[str] | None = None,
    mode: str = "quick",
    allow_initial_full: bool = False,
    source: str | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    tickers = normalize_tickers(raw_tickers)
    normalized_source = _normalize_data_source(settings, source)
    payload = (
        await build_full_payload(settings, tickers, source=normalized_source)
        if mode == "full"
        else await build_quick_payload(settings, tickers, source=normalized_source, allow_initial_full=allow_initial_full)
    )
    payload["summary"]["elapsedSeconds"] = round(time.perf_counter() - started, 2)
    payload["summary"]["dataSource"] = normalized_source
    return payload


async def search_option_tickers(settings: Settings, query: str) -> list[dict[str, Any]]:
    text = query.strip().upper()
    if not text:
        return []
    params = {
        "ticker.gte": text,
        "market": "stocks",
        "active": "true",
        "sort": "ticker",
        "order": "asc",
        "limit": 100,
    }
    async with httpx.AsyncClient() as client:
        payload = await _get_json(client, settings, "/v3/reference/tickers", params)
    rows = payload.get("results") or []
    preferred = [item for item in rows if str(item.get("type", "")).upper() in {"CS", "ADRC"}]
    selected = preferred or rows
    return [
        {
            "ticker": item.get("ticker"),
            "name": item.get("name"),
            "type": item.get("type"),
            "exchange": item.get("primary_exchange"),
        }
        for item in selected[:25]
        if item.get("ticker")
    ]
