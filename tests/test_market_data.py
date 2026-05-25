from app.services.market_data import (
    normalize_financials,
    normalize_snapshot,
    normalize_ticker_overview,
    normalize_yahoo_chart,
    normalize_yahoo_quote,
    normalize_yahoo_quote_item,
    static_global_fundamentals,
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
            "day": {
                "v": 169339208,
                "dv": "169339208.6",
                "vw": 216.8426,
                "o": 220,
                "h": 221,
                "l": 214,
            },
            "lastTrade": {"p": 214.2801},
            "min": {"c": 214.25},
            "prevDay": {"c": 219.51},
        }
    )

    assert normalized["ticker"] == "NVDA"
    assert normalized["price"] == 214.2801
    assert normalized["change_percent"] == -2.5
    assert normalized["volume"] == 169339208
    assert normalized["dollar_volume"] == 169339208 * 216.8426
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


def test_normalize_yahoo_chart_extracts_global_quote():
    normalized = normalize_yahoo_chart(
        {
            "chart": {
                "result": [
                    {
                        "meta": {
                            "currency": "JPY",
                            "exchangeName": "JPX",
                            "regularMarketPrice": 5300,
                            "chartPreviousClose": 5178,
                            "regularMarketTime": 1779456000,
                        },
                        "indicators": {
                            "quote": [
                                {
                                    "open": [5243],
                                    "high": [5332],
                                    "low": [5183],
                                    "close": [5300],
                                    "volume": [3827500],
                                }
                            ]
                        },
                    }
                ]
            }
        },
        "2802.T",
    )

    assert normalized["ticker"] == "2802.T"
    assert normalized["price"] == 5300
    assert normalized["change"] == 122
    assert round(normalized["change_percent"], 2) == 2.36
    assert normalized["dollar_volume"] == 3827500 * 5300
    assert normalized["currency"] == "JPY"
    assert normalized["provider"] == "Yahoo Chart"


def test_normalize_yahoo_quote_item_extracts_low_frequency_fundamentals():
    normalized = normalize_yahoo_quote_item(
        {
            "symbol": "000660.KS",
            "marketCap": 1_377_828_327_129_088,
            "sharesOutstanding": 709_854_891,
            "regularMarketPrice": 1_941_000,
            "currency": "KRW",
            "financialCurrency": "KRW",
            "priceEpsCurrentYear": 6.568369,
        }
    )

    assert normalized["ticker"] == "000660.KS"
    assert normalized["market_cap"] == 1_377_828_327_129_088
    assert normalized["weighted_shares_outstanding"] == 709_854_891
    assert normalized["pe_ratio"] == 6.568369
    assert normalized["fundamentals_currency"] == "KRW"
    assert normalized["fundamentals_provider"] == "Yahoo Quote"


def test_normalize_yahoo_quote_ignores_negative_pe_but_keeps_market_cap():
    normalized = normalize_yahoo_quote(
        {
            "quoteResponse": {
                "result": [
                        {
                            "symbol": "IQE.L",
                            "marketCap": 448_296_128,
                            "trailingPE": None,
                            "forwardPE": -36.6,
                            "priceEpsCurrentYear": -1828.5372,
                            "epsTrailingTwelveMonths": -0.05,
                        }
                ]
            }
        }
    )

    assert normalized["IQE.L"]["market_cap"] == 448_296_128
    assert "pe_ratio" not in normalized["IQE.L"]
    assert normalized["IQE.L"]["pe_note"] == "N/M"


def test_static_global_fundamentals_covers_known_non_us_names():
    rows = static_global_fundamentals(["000660.KS", "IQE.L", "UNKNOWN.X"])

    assert rows["000660.KS"]["market_cap"]
    assert rows["000660.KS"]["pe_ratio"]
    assert rows["IQE.L"]["market_cap"]
    assert rows["IQE.L"]["pe_note"] == "N/M"
    assert "UNKNOWN.X" not in rows
