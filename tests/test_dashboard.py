from app.models import WatchlistMention, utcnow
from app.services.dashboard import (
    dashboard_tickers,
    get_dashboard_snapshot,
    mention_rows,
    normalize_ticker,
)
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
    assert not any(
        row["ticker"].endswith((".SZ", ".SS", ".SH", ".BJ")) for row in snapshot["rows"]
    )
    assert not any(
        ticker.endswith((".SZ", ".SS", ".SH", ".BJ")) for ticker in dashboard_tickers()
    )


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
    fundamentals = next(
        source for source in snapshot["source_status"] if source["name"] == "Fundamentals"
    )
    assert fundamentals["status"] == "pending"


def test_dashboard_snapshot_includes_dynamic_positive_mentions():
    mention = WatchlistMention(
        ticker="XYZ",
        reason="Serenity source is constructive on the setup.",
        source_url="https://x.com/aleabitoreddit/status/1",
        sentiment="positive",
        created_at=utcnow(),
    )
    dynamic_rows = mention_rows([mention])
    snapshot = get_dashboard_snapshot(
        MarketDataResult(
            provider="Yahoo Chart",
            status="live",
            rows={
                "XYZ": {
                    "price": 12.5,
                    "change_percent": 3.2,
                    "currency": "EUR",
                    "provider": "Yahoo Chart",
                }
            },
            eligible_count=1,
            loaded_count=1,
            fundamentals_loaded_count=1,
            detail="Yahoo Chart fallback populated 1/1 missing/global tickers.",
        ),
        dynamic_rows,
        [mention],
    )

    row = next(item for item in snapshot["rows"] if item["ticker"] == "XYZ")
    assert any(category["slug"] == "serenity-alert" for category in snapshot["categories"])
    assert row["category"] == "serenity-alert"
    assert row["price"] == 12.5
    assert row["currency"] == "EUR"
    assert row["source_url"] == "https://x.com/aleabitoreddit/status/1"
    fundamentals = next(
        source for source in snapshot["source_status"] if source["name"] == "Fundamentals"
    )
    assert fundamentals["status"] == "live"


def test_dashboard_excludes_dynamic_mainland_positive_mentions():
    mention = WatchlistMention(
        ticker=" 300308.SZ ",
        reason="Positive source mention.",
        source_url="https://x.com/aleabitoreddit/status/2",
        sentiment="positive",
        created_at=utcnow(),
    )

    assert mention_rows([mention]) == []


def test_normalize_ticker_strips_sentence_punctuation_and_known_aliases():
    assert normalize_ticker("$MSFT.") == "MSFT"
    assert normalize_ticker("TSEM.") == "TSEM"
    assert normalize_ticker("SIVE.") == "SIVE.ST"
    assert normalize_ticker("IQE") == "IQE.L"
    assert normalize_ticker("SOI.") == "SOI.PA"
    assert normalize_ticker("XFAB.") == "XFAB.PA"
    assert normalize_ticker("LPK") == "LPK.DE"


def test_mention_rows_dedupes_canonical_mentions_against_static_rows():
    mentions = [
        WatchlistMention(
            ticker="MSFT.",
            reason="Sentence punctuation should not create a duplicate.",
            sentiment="positive",
            created_at=utcnow(),
        ),
        WatchlistMention(
            ticker="SIVE",
            reason="Known suffix alias should merge into SIVE.ST.",
            sentiment="positive",
            created_at=utcnow(),
        ),
        WatchlistMention(
            ticker="IQE.",
            reason="Known suffix alias should merge into IQE.L.",
            sentiment="positive",
            created_at=utcnow(),
        ),
        WatchlistMention(
            ticker="XFAB.",
            reason="First XFAB mention.",
            sentiment="positive",
            created_at=utcnow(),
        ),
        WatchlistMention(
            ticker="XFAB",
            reason="Duplicate XFAB mention.",
            sentiment="positive",
            created_at=utcnow(),
        ),
    ]

    rows = mention_rows(mentions)

    assert [row["ticker"] for row in rows] == ["XFAB.PA"]


def test_dashboard_snapshot_treats_zero_market_rows_as_missing():
    mention = WatchlistMention(
        ticker="XFAB.",
        reason="Zero quote should not look live.",
        sentiment="positive",
        created_at=utcnow(),
    )
    dynamic_rows = mention_rows([mention])

    snapshot = get_dashboard_snapshot(
        MarketDataResult(
            provider="Yahoo Chart",
            status="live",
            rows={
                "XFAB.PA": {
                    "price": 0,
                    "change_percent": 0,
                    "dollar_volume": 0,
                    "market_cap": 0,
                    "pe_ratio": 0,
                    "price_mode": "live",
                }
            },
            eligible_count=1,
            loaded_count=1,
            detail="Synthetic zero row.",
        ),
        dynamic_rows,
        [mention],
    )

    row = next(item for item in snapshot["rows"] if item["ticker"] == "XFAB.PA")
    assert row["price"] is None
    assert row["change_percent"] is None
    assert row["dollar_volume"] is None
    assert row["market_cap"] is None
    assert row["pe_ratio"] is None
    assert row["price_mode"] == "missing"
