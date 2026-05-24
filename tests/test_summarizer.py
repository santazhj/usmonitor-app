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
