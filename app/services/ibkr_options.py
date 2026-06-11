from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable


class IbkrOptionsError(RuntimeError):
    pass


ProgressCallback = Callable[[dict[str, Any]], None]

_CLIENT_ID_LOCK = threading.Lock()
_CLIENT_ID_COUNTER = 0


def _next_auto_client_id(base_client_id: int) -> int:
    global _CLIENT_ID_COUNTER
    with _CLIENT_ID_LOCK:
        counter = _CLIENT_ID_COUNTER
        _CLIENT_ID_COUNTER += 1
    return base_client_id + (os.getpid() % 1000) * 100 + counter


def _load_ibapi():
    try:
        from ibapi.client import EClient
        from ibapi.contract import Contract
        from ibapi.wrapper import EWrapper
    except ImportError as exc:
        raise IbkrOptionsError("ibapi is not installed. Run pip install ibapi.") from exc
    return EClient, Contract, EWrapper


def _is_valid_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number and abs(number) < 1e100 and number >= 0


def _is_finite_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return number == number and abs(number) < 1e100


def _to_int(value: Any, default: int = 0) -> int:
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _expiry_to_iso(value: str) -> str:
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def _expiry_to_ib(value: str) -> str:
    return value.replace("-", "")


def _format_strike(value: float) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".")


def _ibkr_option_key(symbol: str, expiry: str, right: str, strike: float) -> str:
    return f"IBKR:{symbol.upper()}:{expiry}:{right.upper()}:{_format_strike(strike)}"


def _parse_ibkr_option_key(value: str) -> tuple[str, str, str, float]:
    match = re.fullmatch(r"IBKR:([A-Z0-9.\-]+):(\d{8}):(C|P):([0-9.]+)", value.upper())
    if not match:
        raise IbkrOptionsError(f"Unsupported IBKR option key: {value}")
    symbol, expiry, right, strike = match.groups()
    return symbol, expiry, right, float(strike)


def _rank_secdef(row: dict[str, Any], symbol: str, expirations: list[str], strikes: list[float]) -> tuple[int, int, int, int]:
    exchange_rank = {"SMART": 5, "CBOE": 4, "BOX": 3, "ISE": 3, "PHLX": 3, "AMEX": 2}
    trading_class = str(row.get("tradingClass") or "").upper()
    exchange = str(row.get("exchange") or "").upper()
    return (
        1 if trading_class == symbol.upper() else 0,
        min(len(expirations), 60),
        min(len(strikes), 500),
        exchange_rank.get(exchange, 1),
    )


@dataclass
class _QuoteState:
    bid: float = 0.0
    ask: float = 0.0
    last: float = 0.0
    bid_size: int = 0
    ask_size: int = 0
    delta: float | None = None
    gamma: float | None = None
    vega: float | None = None
    theta: float | None = None
    rho: float | None = None
    implied_volatility: float | None = None
    model_price: float | None = None
    underlying_price: float | None = None
    put_open_interest: int = 0
    put_volume: int = 0
    last_updated_ns: int = field(default_factory=lambda: int(time.time_ns()))


def _quote_signature(quote: _QuoteState) -> tuple[Any, ...]:
    return (
        quote.bid,
        quote.ask,
        quote.last,
        quote.bid_size,
        quote.ask_size,
        quote.delta,
        quote.gamma,
        quote.vega,
        quote.theta,
        quote.rho,
        quote.implied_volatility,
        quote.model_price,
        quote.underlying_price,
        quote.put_open_interest,
        quote.put_volume,
    )


def _has_quote_data(quote: _QuoteState) -> bool:
    return any(value not in {None, 0, 0.0} for value in _quote_signature(quote))


def _has_greeks(quote: _QuoteState) -> bool:
    return quote.delta is not None and quote.implied_volatility is not None


class _IbkrApp:
    def __init__(self) -> None:
        EClient, _Contract, EWrapper = _load_ibapi()

        class App(EWrapper, EClient):  # type: ignore[misc, valid-type]
            def __init__(self, owner: _IbkrApp) -> None:
                EWrapper.__init__(self)
                EClient.__init__(self, self)
                self.owner = owner

        self.app = App(self)
        self.ready = threading.Event()
        self._lock = threading.Lock()
        self._next_req_id = 1
        self.errors: dict[int, list[str]] = {}
        self.contract_details: dict[int, list[Any]] = {}
        self.contract_events: dict[int, threading.Event] = {}
        self.secdef_results: dict[int, list[dict[str, Any]]] = {}
        self.secdef_events: dict[int, threading.Event] = {}
        self.historical_rows: dict[int, list[dict[str, Any]]] = {}
        self.historical_events: dict[int, threading.Event] = {}
        self.quotes: dict[int, _QuoteState] = {}
        self.quote_events: dict[int, threading.Event] = {}
        self.thread: threading.Thread | None = None

        def nextValidId(this: Any, orderId: int) -> None:  # noqa: N802
            self.ready.set()

        def error(this: Any, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:  # noqa: N802
            if errorCode in {2104, 2106, 2158, 2107, 2108}:
                return
            with self._lock:
                self.errors.setdefault(reqId, []).append(f"IBKR {errorCode}: {errorString}")
                event = self.contract_events.get(reqId) or self.secdef_events.get(reqId) or self.historical_events.get(reqId) or self.quote_events.get(reqId)
            if event:
                event.set()

        def contractDetails(this: Any, reqId: int, contractDetails: Any) -> None:  # noqa: N802
            with self._lock:
                self.contract_details.setdefault(reqId, []).append(contractDetails.contract)

        def contractDetailsEnd(this: Any, reqId: int) -> None:  # noqa: N802
            event = self.contract_events.get(reqId)
            if event:
                event.set()

        def securityDefinitionOptionParameter(this: Any, reqId: int, exchange: str, underlyingConId: int, tradingClass: str, multiplier: str, expirations: set[str], strikes: set[float]) -> None:  # noqa: N802
            with self._lock:
                self.secdef_results.setdefault(reqId, []).append(
                    {
                        "exchange": exchange,
                        "tradingClass": tradingClass,
                        "multiplier": multiplier,
                        "expirations": set(expirations),
                        "strikes": set(strikes),
                    }
                )

        def securityDefinitionOptionParameterEnd(this: Any, reqId: int) -> None:  # noqa: N802
            event = self.secdef_events.get(reqId)
            if event:
                event.set()

        def historicalData(this: Any, reqId: int, bar: Any) -> None:  # noqa: N802
            with self._lock:
                self.historical_rows.setdefault(reqId, []).append({"date": bar.date, "c": float(bar.close)})

        def historicalDataEnd(this: Any, reqId: int, start: str, end: str) -> None:  # noqa: N802
            event = self.historical_events.get(reqId)
            if event:
                event.set()

        def tickPrice(this: Any, reqId: int, tickType: int, price: float, attrib: Any) -> None:  # noqa: N802
            if not _is_valid_number(price):
                return
            quote = self.quotes.setdefault(reqId, _QuoteState())
            if tickType == 1:
                quote.bid = float(price)
            elif tickType == 2:
                quote.ask = float(price)
            elif tickType in {4, 9, 68}:
                quote.last = float(price)
            quote.last_updated_ns = int(time.time_ns())
            event = self.quote_events.get(reqId)
            if event and (quote.bid > 0 or quote.ask > 0):
                event.set()

        def tickSize(this: Any, reqId: int, tickType: int, size: Any) -> None:  # noqa: N802
            quote = self.quotes.setdefault(reqId, _QuoteState())
            if tickType == 0:
                quote.bid_size = _to_int(size)
            elif tickType == 3:
                quote.ask_size = _to_int(size)
            elif tickType == 28:
                quote.put_open_interest = _to_int(size)
            elif tickType == 30:
                quote.put_volume = _to_int(size)
            quote.last_updated_ns = int(time.time_ns())

        def tickOptionComputation(this: Any, reqId: int, tickType: int, tickAttrib: int, impliedVolatility: float, delta: float, optPrice: float, pvDividend: float, gamma: float, vega: float, theta: float, undPrice: float) -> None:  # noqa: N802
            quote = self.quotes.setdefault(reqId, _QuoteState())
            if _is_valid_number(impliedVolatility):
                quote.implied_volatility = float(impliedVolatility)
            if _is_finite_number(delta):
                quote.delta = float(delta)
            if _is_finite_number(gamma):
                quote.gamma = float(gamma)
            if _is_finite_number(vega):
                quote.vega = float(vega)
            if _is_finite_number(theta):
                quote.theta = float(theta)
            if _is_valid_number(optPrice):
                quote.model_price = float(optPrice)
            if _is_valid_number(undPrice):
                quote.underlying_price = float(undPrice)
            quote.last_updated_ns = int(time.time_ns())
            event = self.quote_events.get(reqId)
            if event:
                event.set()

        def tickSnapshotEnd(this: Any, reqId: int) -> None:  # noqa: N802
            event = self.quote_events.get(reqId)
            if event:
                event.set()

        self.app.nextValidId = nextValidId.__get__(self.app, App)
        self.app.error = error.__get__(self.app, App)
        self.app.contractDetails = contractDetails.__get__(self.app, App)
        self.app.contractDetailsEnd = contractDetailsEnd.__get__(self.app, App)
        self.app.securityDefinitionOptionParameter = securityDefinitionOptionParameter.__get__(self.app, App)
        self.app.securityDefinitionOptionParameterEnd = securityDefinitionOptionParameterEnd.__get__(self.app, App)
        self.app.historicalData = historicalData.__get__(self.app, App)
        self.app.historicalDataEnd = historicalDataEnd.__get__(self.app, App)
        self.app.tickPrice = tickPrice.__get__(self.app, App)
        self.app.tickSize = tickSize.__get__(self.app, App)
        self.app.tickOptionComputation = tickOptionComputation.__get__(self.app, App)
        self.app.tickSnapshotEnd = tickSnapshotEnd.__get__(self.app, App)

    def connect(self, host: str, port: int, client_id: int, timeout: float, market_data_type: int) -> None:
        if self.app.isConnected():
            return
        self.app.connect(host, port, client_id)
        self.thread = threading.Thread(target=self.app.run, name="ibkr-tws-api", daemon=True)
        self.thread.start()
        if not self.ready.wait(timeout):
            self.disconnect()
            raise IbkrOptionsError(f"Could not connect to IBKR TWS API at {host}:{port}. Check TWS/Gateway API settings.")
        self.app.reqMarketDataType(market_data_type)

    def disconnect(self) -> None:
        try:
            self.app.disconnect()
        except Exception:
            pass

    def next_req_id(self) -> int:
        with self._lock:
            req_id = self._next_req_id
            self._next_req_id += 1
            return req_id

    def pop_errors(self, req_id: int) -> list[str]:
        with self._lock:
            return self.errors.pop(req_id, [])


class IbkrOptionsClient:
    def __init__(
        self,
        host: str,
        port: int,
        client_id: int,
        timeout_seconds: float,
        market_data_type: int,
        max_option_quotes: int,
        snapshot_timeout_seconds: float,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.host = host
        self.port = int(port)
        self.client_id = _next_auto_client_id(int(client_id))
        self.timeout_seconds = float(timeout_seconds)
        self.market_data_type = int(market_data_type)
        self.max_option_quotes = int(max_option_quotes)
        self.snapshot_timeout_seconds = float(snapshot_timeout_seconds)
        self.progress_callback = progress_callback
        self._ib = _IbkrApp()
        self._connected = False
        self._connect_error: str | None = None

    def _report(self, **event: Any) -> None:
        if self.progress_callback:
            self.progress_callback({"source": "ibkr", **event})

    def _connect(self) -> None:
        if self._connected:
            return
        if self._connect_error:
            raise IbkrOptionsError(self._connect_error)
        try:
            self._ib.connect(self.host, self.port, self.client_id, self.timeout_seconds, self.market_data_type)
        except IbkrOptionsError as exc:
            self._connect_error = str(exc)
            raise
        self._connected = True

    def disconnect(self) -> None:
        self._ib.disconnect()
        self._connected = False

    def _stock_contract(self, ticker: str) -> Any:
        _EClient, Contract, _EWrapper = _load_ibapi()
        contract = Contract()
        contract.symbol = ticker.upper()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    def _option_contract(self, symbol: str, expiry: str, right: str, strike: float, trading_class: str = "", exchange: str = "SMART") -> Any:
        _EClient, Contract, _EWrapper = _load_ibapi()
        contract = Contract()
        contract.symbol = symbol.upper()
        contract.secType = "OPT"
        contract.exchange = exchange
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = expiry
        contract.strike = float(strike)
        contract.right = right.upper()
        contract.multiplier = "100"
        if trading_class:
            contract.tradingClass = trading_class
        return contract

    def _get_contract_details(self, contract: Any) -> list[Any]:
        self._connect()
        req_id = self._ib.next_req_id()
        event = threading.Event()
        self._ib.contract_events[req_id] = event
        self._ib.app.reqContractDetails(req_id, contract)
        event.wait(self.timeout_seconds)
        errors = self._ib.pop_errors(req_id)
        details = self._ib.contract_details.pop(req_id, [])
        self._ib.contract_events.pop(req_id, None)
        if errors and not details:
            raise IbkrOptionsError("; ".join(errors))
        return details

    def _get_contract_details_batch(self, contracts: list[Any]) -> list[Any]:
        self._connect()
        req_ids: list[int] = []
        for contract in contracts:
            req_id = self._ib.next_req_id()
            self._ib.contract_events[req_id] = threading.Event()
            req_ids.append(req_id)
            self._ib.app.reqContractDetails(req_id, contract)
        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            if all(self._ib.contract_events[req_id].is_set() for req_id in req_ids):
                break
            time.sleep(0.05)
        resolved: list[Any] = []
        for req_id in req_ids:
            details = self._ib.contract_details.pop(req_id, [])
            if details:
                resolved.append(details[0])
            self._ib.contract_events.pop(req_id, None)
            self._ib.pop_errors(req_id)
        return resolved

    def _get_stock_conid(self, ticker: str) -> int:
        details = self._get_contract_details(self._stock_contract(ticker))
        if not details:
            raise IbkrOptionsError(f"IBKR could not resolve stock contract for {ticker}.")
        return int(details[0].conId)

    def get_stock_bars(self, ticker: str, start: date, end: date) -> list[dict[str, Any]]:
        self._connect()
        req_id = self._ib.next_req_id()
        event = threading.Event()
        self._ib.historical_events[req_id] = event
        days = max(1, min(365, (end - start).days + 1))
        self._ib.app.reqHistoricalData(req_id, self._stock_contract(ticker), "", f"{days} D", "1 day", "TRADES", 1, 1, False, [])
        event.wait(max(self.timeout_seconds, 20.0))
        errors = self._ib.pop_errors(req_id)
        rows = self._ib.historical_rows.pop(req_id, [])
        self._ib.historical_events.pop(req_id, None)
        if errors and not rows:
            raise IbkrOptionsError("; ".join(errors))
        return rows

    def _get_stock_snapshot(self, ticker: str) -> _QuoteState:
        quotes = self._request_quotes([self._stock_contract(ticker)], context=ticker)
        return quotes[0] if quotes else _QuoteState()

    def _get_secdef(self, underlying: str, con_id: int) -> list[dict[str, Any]]:
        self._connect()
        req_id = self._ib.next_req_id()
        event = threading.Event()
        self._ib.secdef_events[req_id] = event
        self._ib.app.reqSecDefOptParams(req_id, underlying.upper(), "", "STK", con_id)
        event.wait(self.timeout_seconds)
        errors = self._ib.pop_errors(req_id)
        rows = self._ib.secdef_results.pop(req_id, [])
        self._ib.secdef_events.pop(req_id, None)
        if errors and not rows:
            raise IbkrOptionsError("; ".join(errors))
        return rows

    def _request_quotes(self, contracts: list[Any], context: str = "") -> list[_QuoteState]:
        self._connect()
        self._report(stage="quotes", ticker=context, message=f"{context}: requesting {len(contracts)} quotes", quoteRequests=len(contracts), quotesWithBidAsk=0, quotesWithGreeks=0)
        req_ids: list[int] = []
        for contract in contracts:
            req_id = self._ib.next_req_id()
            self._ib.quotes[req_id] = _QuoteState()
            self._ib.quote_events[req_id] = threading.Event()
            req_ids.append(req_id)
            self._ib.app.reqMktData(req_id, contract, "100,101,104,106", False, False, [])
        deadline = time.monotonic() + self.snapshot_timeout_seconds
        min_wait_until = time.monotonic() + min(2.5, self.snapshot_timeout_seconds)
        last_signature = tuple(_quote_signature(self._ib.quotes[req_id]) for req_id in req_ids)
        last_change = time.monotonic()
        while time.monotonic() < deadline:
            signatures = tuple(_quote_signature(self._ib.quotes[req_id]) for req_id in req_ids)
            if signatures != last_signature:
                last_signature = signatures
                last_change = time.monotonic()
            with_bid_ask = sum(1 for req_id in req_ids if (self._ib.quotes[req_id].bid > 0 and self._ib.quotes[req_id].ask > 0) or self._ib.errors.get(req_id))
            with_greeks = sum(1 for req_id in req_ids if _has_greeks(self._ib.quotes[req_id]) or self._ib.errors.get(req_id))
            observed = sum(1 for req_id in req_ids if _has_quote_data(self._ib.quotes[req_id]) or self._ib.errors.get(req_id))
            if with_bid_ask == len(req_ids) and with_greeks == len(req_ids):
                break
            stable = time.monotonic() - last_change >= 1.0
            if time.monotonic() >= min_wait_until and stable and (with_bid_ask == len(req_ids) or observed >= max(1, int(len(req_ids) * 0.75))):
                break
            time.sleep(0.15)
        quotes = [self._ib.quotes.get(req_id, _QuoteState()) for req_id in req_ids]
        with_bid_ask = sum(1 for quote in quotes if quote.bid > 0 and quote.ask > 0)
        with_greeks = sum(1 for quote in quotes if _has_greeks(quote))
        self._report(stage="quotes_done", ticker=context, message=f"{context}: received {with_bid_ask}/{len(quotes)} bid/ask quotes, {with_greeks}/{len(quotes)} Greeks", quoteRequests=len(quotes), quotesWithBidAsk=with_bid_ask, quotesWithGreeks=with_greeks)
        for req_id in req_ids:
            try:
                self._ib.app.cancelMktData(req_id)
            except Exception:
                pass
            self._ib.quote_events.pop(req_id, None)
            self._ib.pop_errors(req_id)
        return quotes

    def _quote_to_raw(self, contract: Any, quote: _QuoteState, fallback_spot: float = 0.0) -> dict[str, Any]:
        spot = quote.underlying_price or fallback_spot
        expiry = _expiry_to_iso(str(contract.lastTradeDateOrContractMonth))
        option_key = _ibkr_option_key(contract.symbol, str(contract.lastTradeDateOrContractMonth), contract.right, float(contract.strike))
        return {
            "details": {
                "ticker": option_key,
                "underlying_ticker": contract.symbol.upper(),
                "contract_type": "put" if contract.right.upper() == "P" else "call",
                "expiration_date": expiry,
                "strike_price": float(contract.strike),
                "shares_per_contract": 100,
            },
            "last_quote": {
                "bid": quote.bid,
                "ask": quote.ask,
                "bid_size": quote.bid_size,
                "ask_size": quote.ask_size,
                "last_updated": quote.last_updated_ns,
            },
            "greeks": {
                "delta": quote.delta,
                "gamma": quote.gamma,
                "vega": quote.vega,
                "theta": quote.theta,
                "rho": quote.rho,
            },
            "implied_volatility": quote.implied_volatility,
            "open_interest": quote.put_open_interest,
            "underlying_asset": {"ticker": contract.symbol.upper(), "price": spot},
            "day": {"volume": quote.put_volume},
        }

    def get_option_chain(self, underlying: str, expiration_date_gte: str, expiration_date_lte: str, limit: int = 250) -> list[dict[str, Any]]:
        symbol = underlying.upper()
        self._report(stage="contract", ticker=symbol, message=f"{symbol}: resolving stock contract")
        con_id = self._get_stock_conid(symbol)
        self._report(stage="stock_snapshot", ticker=symbol, message=f"{symbol}: loading stock snapshot")
        stock_quote = self._get_stock_snapshot(symbol)
        spot = stock_quote.underlying_price or stock_quote.last
        if not spot and stock_quote.bid and stock_quote.ask:
            spot = (stock_quote.bid + stock_quote.ask) / 2
        if not spot:
            spot = stock_quote.bid or stock_quote.ask
        if not spot:
            bars = self.get_stock_bars(symbol, date.today(), date.today())
            spot = float(bars[-1]["c"]) if bars else 0.0
        if not spot:
            raise IbkrOptionsError(f"IBKR could not get an underlying price for {symbol}.")

        self._report(stage="secdef", ticker=symbol, message=f"{symbol}: loading option expirations and strikes")
        min_expiry = _expiry_to_ib(expiration_date_gte)
        max_expiry = _expiry_to_ib(expiration_date_lte)
        secdefs = self._get_secdef(symbol, con_id)
        if not secdefs:
            raise IbkrOptionsError(f"IBKR returned no option parameters for {symbol}.")

        candidates: list[tuple[tuple[int, int, int, int], dict[str, Any], list[str], list[float]]] = []
        for row in secdefs:
            expirations = sorted(exp for exp in row["expirations"] if min_expiry <= exp <= max_expiry and len(exp) == 8)
            strikes = sorted(float(strike) for strike in row["strikes"] if 0 < float(strike) < float(spot))
            if expirations and strikes:
                candidates.append((_rank_secdef(row, symbol, expirations, strikes), row, expirations, strikes))
        candidates.sort(key=lambda item: item[0], reverse=True)
        if not candidates:
            return []

        for _score, secdef, expirations, strikes in candidates:
            trading_class = str(secdef.get("tradingClass") or "")
            exchange = str(secdef.get("exchange") or "SMART")
            pairs: list[tuple[float, str, float]] = []
            for expiry in expirations:
                for strike in strikes:
                    distance = abs((float(spot) - strike) / float(spot) - 0.10)
                    pairs.append((distance, expiry, strike))
            pairs.sort(key=lambda item: (item[0], item[1], -item[2]))
            quote_limit = min(limit, self.max_option_quotes, len(pairs))
            attempt_limit = min(len(pairs), max(quote_limit * 3, quote_limit + 12))
            self._report(stage="resolve_options", ticker=symbol, message=f"{symbol}: resolving up to {quote_limit} option contracts", quoteRequests=quote_limit, quotesWithBidAsk=0, quotesWithGreeks=0)
            attempts = [
                self._option_contract(symbol, expiry, "P", strike, trading_class=trading_class, exchange=exchange)
                for _, expiry, strike in pairs[:attempt_limit]
            ]
            contracts: list[Any] = []
            batch_size = max(quote_limit * 2, quote_limit + 8)
            for start in range(0, len(attempts), batch_size):
                contracts.extend(self._get_contract_details_batch(attempts[start : start + batch_size]))
                if len(contracts) >= quote_limit:
                    contracts = contracts[:quote_limit]
                    break
            if contracts:
                quotes = self._request_quotes(contracts, context=symbol)
                return [self._quote_to_raw(contract, quote, fallback_spot=float(spot)) for contract, quote in zip(contracts, quotes)]
        raise IbkrOptionsError(f"IBKR could not resolve any option contracts for {symbol}.")

    def get_option_snapshot(self, underlying: str, option_ticker: str) -> dict[str, Any]:
        symbol, expiry, right, strike = _parse_ibkr_option_key(option_ticker)
        contract = self._option_contract(symbol or underlying.upper(), expiry, right, strike)
        details = self._get_contract_details(contract)
        if details:
            contract = details[0]
        quote = self._request_quotes([contract], context=symbol)[0]
        return self._quote_to_raw(contract, quote)
