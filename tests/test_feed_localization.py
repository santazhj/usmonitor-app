from app.config import Settings
from app.models import AlertSummary, XPost
from app.services.feed_localization import (
    LOCALIZATION_CACHE_KEY,
    LOCALIZATION_ROOT_KEY,
    fallback_zh_payload,
    localize_feed_for_zh,
)


class FakeDb:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


def summary_with_english_post() -> AlertSummary:
    post = XPost(
        tweet_id="1",
        source_id="source",
        author_handle="aleabitoreddit",
        text=(
            "Did you listen anon? $SIVE is extremely early. "
            "We're about to see a ton of institutional inflow from Blackrock, "
            "Vanguard, MSCI, Nasdaq."
        ),
        url="https://x.com/aleabitoreddit/status/1",
        raw_json={},
    )
    return AlertSummary(
        id="summary-1",
        post=post,
        monitor_list_id="list",
        title="Serenity new post",
        notification_text="@aleabitoreddit: Did you listen anon? $SIVE is extremely early...",
        bullets=["Did you listen anon? $SIVE is extremely early."],
        tickers=["SIVE.ST"],
        why_it_matters="English fallback",
        risks=[],
        source_url=post.url,
    )


def test_fallback_zh_payload_uses_finance_aware_chinese_preview():
    payload = fallback_zh_payload(summary_with_english_post())

    assert payload["title"] == "Serenity 新帖提醒"
    assert "$SIVE.ST" in payload["notification_text"]
    assert "机构资金流" in payload["notification_text"]
    assert "institutional" not in payload["notification_text"].lower()


def test_localize_feed_for_zh_caches_fallback_without_api_key():
    summary = summary_with_english_post()
    db = FakeDb()

    localized = localize_feed_for_zh(Settings(openai_api_key=""), db, [summary])

    assert localized[summary.id]["title"] == "Serenity 新帖提醒"
    assert db.commits == 1
    cached = summary.post.raw_json[LOCALIZATION_ROOT_KEY][LOCALIZATION_CACHE_KEY]
    assert cached["notification_text"] == localized[summary.id]["notification_text"]
