from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import AlertSummary, JobRun, MonitoredSource, XPost, utcnow
from app.services.push import deliver_summary_to_subscribers
from app.services.seed import seed_defaults
from app.services.summarizer import summarize_post
from app.services.x_client import XClient, is_substantive_original, parse_x_datetime


def tweet_url(handle: str, tweet_id: str) -> str:
    return f"https://x.com/{handle}/status/{tweet_id}"


async def poll_sources(db: Session | None = None) -> dict:
    settings = get_settings()
    owns_session = db is None
    if db is None:
        init_db()
        db = SessionLocal()

    job = JobRun(job_name="poll_sources", status="running")
    db.add(job)
    db.commit()

    totals = {"sources": 0, "posts": 0, "summaries": 0, "sent": 0, "failed": 0}
    try:
        seed_defaults(db, settings)
        sources = (
            db.query(MonitoredSource)
            .filter(MonitoredSource.is_active.is_(True))
            .order_by(MonitoredSource.created_at.asc())
            .all()
        )
        if not settings.x_bearer_token:
            job.status = "skipped"
            job.message = "X_BEARER_TOKEN is not configured"
            job.finished_at = utcnow()
            db.commit()
            return totals | {"status": "skipped", "message": job.message}

        client = XClient(settings)
        for source in sources:
            totals["sources"] += 1
            if source.source_type != "x_user":
                continue

            if not source.external_id:
                source.external_id = await client.get_user_id(source.handle)
                db.commit()

            tweets = await client.get_recent_posts(
                source.external_id, source.last_seen_post_id or None
            )
            if not tweets:
                continue

            max_seen = max(tweets, key=lambda item: int(item["id"]))["id"]
            initialize_only = not source.last_seen_post_id and not settings.send_initial_backfill

            for tweet in sorted(tweets, key=lambda item: int(item["id"])):
                if initialize_only:
                    continue
                if not is_substantive_original(tweet):
                    continue
                if db.query(XPost).filter(XPost.tweet_id == tweet["id"]).first():
                    continue

                post = XPost(
                    tweet_id=tweet["id"],
                    source_id=source.id,
                    author_handle=source.handle,
                    text=tweet.get("text", ""),
                    created_at_x=parse_x_datetime(tweet.get("created_at")),
                    url=tweet_url(source.handle, tweet["id"]),
                    raw_json=tweet,
                )
                db.add(post)
                db.commit()
                db.refresh(post)
                totals["posts"] += 1

                output, model = summarize_post(settings, post)
                summary = AlertSummary(
                    post_id=post.id,
                    monitor_list_id=source.monitor_list_id,
                    title=output.title,
                    notification_text=output.notification_text,
                    bullets=output.bullets,
                    tickers=output.tickers,
                    why_it_matters=output.why_it_matters,
                    risks=output.risks,
                    source_url=output.source_url,
                    model=model,
                )
                db.add(summary)
                db.commit()
                db.refresh(summary)
                totals["summaries"] += 1
                delivery_totals = deliver_summary_to_subscribers(db, settings, summary)
                totals["sent"] += delivery_totals["sent"]
                totals["failed"] += delivery_totals["failed"]

            source.last_seen_post_id = max_seen
            db.commit()

        job.status = "completed"
        job.message = "ok"
        job.metadata_json = totals
        job.finished_at = utcnow()
        db.commit()
        return totals | {"status": "completed"}
    except Exception as exc:
        db.rollback()
        job.status = "failed"
        job.message = str(exc)
        job.finished_at = utcnow()
        db.add(job)
        db.commit()
        raise
    finally:
        if owns_session:
            db.close()


def main() -> None:
    result = asyncio.run(poll_sources())
    print(result)


if __name__ == "__main__":
    main()
