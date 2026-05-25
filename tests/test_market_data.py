from app.services.market_data import normalize_snapshot, us_snapshot_tickers


def test_us_snapshot_tickers_skips_non_us_suffixes():
    assert us_snapshot_tickers(["MSFT", "TSM", "000660.KS", "BESI.AS", "XLU"]) == [
        "MSFT",
        "TSM",
        "XLU",
    ]


def test_normalize_snapshot_prefers_last_trade_price():
    normalized = normalize_snapshot(
        {
            "ticker": "NVDA",
            "todaysChangePerc": -2.5,
            "todaysChange": -5.2,
            "updated": 1779494398645461153,
            "day": {"v": 169339208, "dv": "169339208.6", "o": 220, "h": 221, "l": 214},
            "lastTrade": {"p": 214.2801},
            "min": {"c": 214.25},
            "prevDay": {"c": 219.51},
        }
    )

    assert normalized["ticker"] == "NVDA"
    assert normalized["price"] == 214.2801
    assert normalized["change_percent"] == -2.5
    assert normalized["volume"] == 169339208
    assert normalized["updated_at"].startswith("2026-")
