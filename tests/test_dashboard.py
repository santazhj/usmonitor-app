from app.services.dashboard import get_dashboard_snapshot


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
