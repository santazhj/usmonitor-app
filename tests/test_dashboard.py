from app.services.dashboard import get_dashboard_snapshot
from app.services.market_data import MarketDataResult


def test_dashboard_snapshot_has_watchlist_structure():
    snapshot = get_dashboard_snapshot()

    assert snapshot["refresh_interval_seconds"] == 15
    assert snapshot["data_status"] == "provider_pending"
    assert snapshot["metrics"]["tracked_tickers"] == len(snapshot["rows"])
    assert snapshot["metrics"]["categories"] == len(snapshot["categories"])
    assert snapshot["rows"]
    assert {"ticker", "company", "category", "ai_layer", "latest_signal"} <= set(
        snapshot["rows"][0]
    )
    assert snapshot["metrics"]["priced_tickers"] == 0


def test_dashboard_snapshot_merges_market_data():
    market_data = MarketDataResult(
        provider="Massive",
        status="live",
        rows={
            "MSFT": {
                "price": 501.25,
                "change_percent": 1.23,
                "volume": 12345678,
                "dollar_volume": 6_180_000_000,
                "market_cap": 3_100_000_000_000,
                "pe_ratio": 29.8,
                "updated_at": "2026-05-25T14:30:00+00:00",
                "provider": "Massive",
            }
        },
        eligible_count=1,
        loaded_count=1,
        detail="Massive snapshot adapter connected. 1/1 U.S. tickers populated.",
    )

    snapshot = get_dashboard_snapshot(market_data)
    msft = next(row for row in snapshot["rows"] if row["ticker"] == "MSFT")

    assert snapshot["data_status"] == "market_live"
    assert snapshot["metrics"]["priced_tickers"] == 1
    assert msft["price"] == 501.25
    assert msft["change_percent"] == 1.23
    assert msft["volume"] == 12345678
    assert msft["dollar_volume"] == 6_180_000_000
    assert msft["market_cap"] == 3_100_000_000_000
    assert msft["pe_ratio"] == 29.8
