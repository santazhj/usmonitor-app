from app.services.market_data import (
    normalize_financials,
    normalize_snapshot,
    normalize_ticker_overview,
    us_snapshot_tickers,
)


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


def test_normalize_ticker_overview_extracts_market_cap():
    normalized = normalize_ticker_overview(
        {
            "results": {
                "ticker": "MSFT",
                "market_cap": 3_109_319_914_053.28,
                "weighted_shares_outstanding": 7_428_434_704,
            }
        }
    )

    assert normalized["market_cap"] == 3_109_319_914_053.28
    assert normalized["weighted_shares_outstanding"] == 7_428_434_704


def test_normalize_financials_extracts_ttm_eps():
    normalized = normalize_financials(
        {
            "results": [
                {
                    "fiscal_period": "TTM",
                    "end_date": "2026-03-31",
                    "financials": {
                        "income_statement": {
                            "diluted_earnings_per_share": {"value": 16.79},
                            "basic_earnings_per_share": {"value": 16.86},
                        }
                    },
                }
            ]
        }
    )

    assert normalized["ttm_diluted_eps"] == 16.79
    assert normalized["ttm_basic_eps"] == 16.86
    assert normalized["financial_period"] == "TTM"
