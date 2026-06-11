import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.main import feed, lists
from app.models import AlertSummary, Base, MonitorList, MonitoredSource, XPost


class FakeRequest:
    cookies = {}


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_summary(db):
    monitor_list = MonitorList(
        slug="serenity-alert",
        name="Serenity Alert",
        description="Curated market intelligence",
    )
    db.add(monitor_list)
    db.commit()
    db.refresh(monitor_list)

    source = MonitoredSource(
        monitor_list_id=monitor_list.id,
        handle="aleabitoreddit",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    post = XPost(
        tweet_id="tweet-1",
        source_id=source.id,
        author_handle="aleabitoreddit",
        text="$SIVE is early.",
        url="https://x.com/aleabitoreddit/status/1",
        raw_json={},
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    summary = AlertSummary(
        post_id=post.id,
        monitor_list_id=monitor_list.id,
        title="$SIVE 机构资金催化",
        notification_text="$SIVE.ST 仍处早期，关注机构资金流。",
        bullets=["关注机构资金流。"],
        tickers=["SIVE.ST"],
        why_it_matters="用于验证公开 feed。",
        risks=[],
        source_url=post.url,
    )
    db.add(summary)
    db.commit()
    return monitor_list


def test_public_feed_returns_active_monitor_list_summaries_without_login():
    db = make_session()
    seed_summary(db)

    result = asyncio.run(feed(db=db, settings=Settings(openai_api_key=""), lang="en"))

    assert len(result) == 1
    assert result[0]["title"] == "$SIVE 机构资金催化"
    assert result[0]["tickers"] == ["SIVE.ST"]


def test_public_lists_do_not_require_session_cookie():
    db = make_session()
    seed_summary(db)

    result = asyncio.run(lists(FakeRequest(), db=db, settings=Settings()))

    assert result == [
        {
            "id": result[0]["id"],
            "slug": "serenity-alert",
            "name": "Serenity Alert",
            "description": "Curated market intelligence",
            "public_access": True,
            "subscription_active": False,
        }
    ]
