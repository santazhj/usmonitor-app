import asyncio
from datetime import datetime, timezone

from app.config import Settings
from app.services import options_analysis
from app.services.options_analysis import _add_bucket_rankings, _option_record, _payload_from_records


def _raw_option(bid=1.0, ask=1.1):
    return {
        "details": {
            "ticker": "O:TEST260717P00095000",
            "underlying_ticker": "TEST",
            "contract_type": "put",
            "expiration_date": "2026-07-17",
            "strike_price": 95,
            "shares_per_contract": 100,
        },
        "last_quote": {
            "bid": bid,
            "ask": ask,
            "bid_size": 10,
            "ask_size": 10,
            "last_updated": 1781827200000000000,
        },
        "greeks": {"delta": -0.2},
        "implied_volatility": 0.35,
        "open_interest": 1000,
        "underlying_asset": {"ticker": "TEST", "price": 110},
    }


def test_invalid_quote_gets_no_monthly_rank_or_summary_best_score():
    record = _option_record(_raw_option(bid=0.0, ask=0.0), underlying_ticker="TEST")

    ranked = _add_bucket_rankings([record])
    payload = _payload_from_records(["TEST"], ranked, [], source="massive")
    row = payload["underlyings"][0]

    assert row["platform_valid"] is False
    assert row["edge_flag"] == "Data Gap"
    assert row["cycle_put_edge_ratio"] == 0
    assert row["bucket_rank"] == 0
    assert row["monthly_score"] == 0
    assert payload["summary"]["validContracts"] == 0
    assert payload["summary"]["bestMonthlyScore"] is None


def test_quick_no_cache_records_progress_snapshot():
    options_analysis._scan_cache.clear()
    options_analysis._scan_progress.clear()
    settings = Settings(massive_api_key="test")

    payload = asyncio.run(options_analysis.build_quick_payload(settings, ["TEST"], source="massive"))
    progress = options_analysis.options_progress_snapshot(settings, ["TEST"], source="massive")

    assert payload["summary"]["dataSource"] == "massive"
    assert payload["summary"]["fullScanRequired"] is True
    assert progress["mode"] == "quick"
    assert progress["stage"] == "done"
    assert progress["active"] is False
    assert progress["message"] == "Run full scan first"


def test_quick_cached_refresh_records_final_quote_counts(monkeypatch):
    options_analysis._scan_cache.clear()
    options_analysis._scan_progress.clear()
    settings = Settings(massive_api_key="test")
    key = options_analysis._cache_key("massive", ["MU"])
    options_analysis._scan_cache[key] = options_analysis.OptionScanCacheEntry(
        payload={
            "summary": {"dataSource": "massive", "contracts": 1},
            "underlyings": [
                {
                    "ticker": "MU",
                    "option_ticker": "O:MU260717P00630000",
                    "bid": 18.0,
                    "ask": 19.0,
                    "delta": -0.2,
                    "iv": 1.0,
                    "topOptions": [{"option_ticker": "O:MU260717P00630000"}],
                }
            ],
            "errors": [],
            "tickers": ["MU"],
        },
        full_scanned_at=datetime.now(timezone.utc),
    )

    async def fake_refresh_best_option(client, settings, row):
        return {
            **row,
            "bid": 18.7,
            "ask": 19.8,
            "delta": -0.21,
            "iv": 1.05,
            "put_edge_ratio": 2.1,
            "score": 90,
        }

    monkeypatch.setattr(options_analysis, "_refresh_best_option", fake_refresh_best_option)

    payload = asyncio.run(options_analysis.build_quick_payload(settings, ["MU"], source="massive"))
    progress = options_analysis.options_progress_snapshot(settings, ["MU"], source="massive")

    assert payload["summary"]["quickContractsRefreshed"] == 1
    assert progress["completed"] == 1
    assert progress["quoteRequests"] == 1
    assert progress["quotesWithBidAsk"] == 1
    assert progress["quotesWithGreeks"] == 1
