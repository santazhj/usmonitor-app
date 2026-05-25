from app.models import XPost
from app.services.summarizer import fallback_summary


def test_fallback_summary_extracts_tickers_and_disclaimer_risk():
    post = XPost(
        tweet_id="1",
        source_id="source",
        author_handle="aleabitoreddit",
        text="$NVDA and $MU are central to this setup.",
        url="https://x.com/aleabitoreddit/status/1",
        raw_json={},
    )

    summary = fallback_summary(post)

    assert summary.source_url == post.url
    assert summary.tickers == ["MU", "NVDA"]
    assert "不构成投资建议" in summary.risks


def test_fallback_summary_marks_positive_tickers_when_text_is_bullish():
    post = XPost(
        tweet_id="2",
        source_id="source",
        author_handle="aleabitoreddit",
        text="Bullish on $ALAB and $CRDO as AI connectivity beneficiaries.",
        url="https://x.com/aleabitoreddit/status/2",
        raw_json={},
    )

    summary = fallback_summary(post)

    assert summary.positive_tickers == ["ALAB", "CRDO"]
