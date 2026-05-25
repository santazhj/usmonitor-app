from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import AlertSummary, WatchlistMention, XPost
from app.services.summarizer import normalize_ticker, positive_tickers_from_text


def mention_reason(summary: AlertSummary) -> str:
    reason = summary.why_it_matters or summary.notification_text or summary.title
    return " ".join(reason.split())[:500]


def sync_positive_mentions(
    db: Session,
    post: XPost,
    summary: AlertSummary,
    positive_tickers: list[str],
) -> int:
    created = 0
    reason = mention_reason(summary)
    for ticker in sorted({normalize_ticker(item) for item in positive_tickers if item}):
        existing = (
            db.query(WatchlistMention)
            .filter(
                WatchlistMention.summary_id == summary.id,
                WatchlistMention.ticker == ticker,
            )
            .one_or_none()
        )
        if existing:
            continue
        db.add(
            WatchlistMention(
                ticker=ticker,
                sentiment="positive",
                reason=reason,
                source_url=summary.source_url or post.url,
                post_id=post.id,
                summary_id=summary.id,
            )
        )
        created += 1
    if created:
        db.commit()
    return created


def backfill_positive_mentions(db: Session, limit: int = 100) -> int:
    summaries = (
        db.query(AlertSummary)
        .order_by(AlertSummary.created_at.desc())
        .limit(limit)
        .all()
    )
    created = 0
    for summary in summaries:
        if not summary.tickers:
            continue
        existing = (
            db.query(WatchlistMention)
            .filter(WatchlistMention.summary_id == summary.id)
            .first()
        )
        if existing:
            continue
        text = " ".join(
            [
                summary.title or "",
                summary.notification_text or "",
                summary.why_it_matters or "",
                " ".join(summary.bullets or []),
            ]
        )
        positive_tickers = positive_tickers_from_text(text, summary.tickers)
        if summary.post and positive_tickers:
            created += sync_positive_mentions(
                db,
                summary.post,
                summary,
                positive_tickers,
            )
    return created
