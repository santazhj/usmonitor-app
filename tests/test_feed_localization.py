from app.config import Settings
from app.models import AlertSummary, XPost
from app.services.feed_localization import (
    LOCALIZATION_ROOT_KEY,
    existing_chinese_payload,
    fallback_zh_payload,
    localize_feed_for_zh,
    payload_quality_ok,
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

    assert payload["title"] == "$SIVE.ST 机构资金催化"
    assert "$SIVE.ST" in payload["notification_text"]
    assert "机构资金流" in payload["notification_text"]
    assert "institutional" not in payload["notification_text"].lower()


def test_localize_feed_for_zh_does_not_cache_fallback_without_api_key():
    summary = summary_with_english_post()
    db = FakeDb()

    localized = localize_feed_for_zh(Settings(openai_api_key=""), db, [summary])

    assert localized[summary.id]["title"] == "$SIVE.ST 机构资金催化"
    assert db.commits == 0
    assert LOCALIZATION_ROOT_KEY not in summary.post.raw_json


def test_existing_chinese_payload_requires_chinese_notification_body():
    summary = summary_with_english_post()
    summary.title = "Serenity 新帖提醒"
    summary.why_it_matters = "这是中文解释。"

    assert existing_chinese_payload(summary) is None


def test_existing_chinese_payload_rejects_generic_title():
    summary = summary_with_english_post()
    summary.title = "Serenity 新帖提醒"
    summary.notification_text = "$SIVE 还处在很早期，接下来可能看到机构资金流入。"
    summary.why_it_matters = "这是中文解释。"

    assert existing_chinese_payload(summary) is None


def test_payload_quality_rejects_mixed_english_sentence_residue():
    payload = {
        "title": "$SIVE 机构资金催化",
        "notification_text": (
            "作者这条帖子的意思是：$SIVE 还处在非常早期。And we're about to see "
            "a ton of institutional inflow."
        ),
        "bullets": [],
        "why_it_matters": "",
    }

    assert payload_quality_ok(payload) is False


def test_payload_quality_allows_tickers_and_institution_names():
    payload = {
        "title": "$SIVE 机构资金催化",
        "notification_text": (
            "作者认为 $SIVE.ST 还处在很早期，接下来可能看到 BlackRock、"
            "Vanguard、MSCI 和 NASDAQ 相关资金流入。"
        ),
        "bullets": [],
        "why_it_matters": "",
    }

    assert payload_quality_ok(payload) is True


def test_payload_quality_allows_company_and_tech_names():
    payload = {
        "title": "Sivers 上游价值重估",
        "notification_text": (
            "作者认为，Ayar、Celestial、Lightmatter、Lighthorse 这些公司的估值可能已经在"
            "40亿到150亿美元以上，而 Sivers 当前市值约26亿美元，却可能是它们共同的上游"
            "知识产权供应商；这还没把 Poet、TFLN 等线索算进去。"
        ),
        "bullets": [],
        "why_it_matters": "",
    }

    assert payload_quality_ok(payload) is True


def test_payload_quality_rejects_generic_title():
    payload = {
        "title": "Serenity 新帖提醒",
        "notification_text": "$SIVE 还处在很早期，接下来可能看到机构资金流入。",
        "bullets": [],
        "why_it_matters": "",
    }

    assert payload_quality_ok(payload) is False
