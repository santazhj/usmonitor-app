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
