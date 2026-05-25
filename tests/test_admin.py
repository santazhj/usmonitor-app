import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.main import (
    AnalyticsEventRequest,
    MembershipRequest,
    SESSION_COOKIE,
    active_subscription,
    admin_update_membership,
    analytics_event,
    current_payment,
)
from app.models import AnalyticsEvent, Base, ManualPayment, MonitorList, Subscription, User
from app.security import sign_payload


class FakeRequest:
    def __init__(self, cookies=None):
        self.cookies = cookies or {}
        self.headers = {"user-agent": "pytest"}


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_analytics_event_records_authenticated_user():
    db = make_session()
    settings = Settings(secret_key="test-secret")
    user = User(email="member@example.com")
    db.add(user)
    db.commit()
    token = sign_payload(
        {"typ": "session", "uid": user.id},
        settings.secret_key,
        60,
    )

    result = asyncio.run(
        analytics_event(
            AnalyticsEventRequest(
                visitor_id="visitor-123",
                event_type="heartbeat",
                path="/#account",
                duration_seconds=42,
                language="zh",
                viewport="390x844",
            ),
            FakeRequest({SESSION_COOKIE: token}),
            db,
            settings,
        )
    )

    event = db.query(AnalyticsEvent).one()
    assert result["ok"] is True
    assert event.user_id == user.id
    assert event.event_type == "heartbeat"
    assert event.duration_seconds == 42


def test_admin_membership_toggle_grants_and_revokes_subscription():
    db = make_session()
    admin = User(email="owner@example.com", is_admin=True)
    user = User(email="friend@example.com")
    monitor_list = MonitorList(slug="serenity-alert", name="Serenity Alert")
    db.add_all([admin, user, monitor_list])
    db.commit()

    grant = asyncio.run(
        admin_update_membership(
            user.id,
            MembershipRequest(active=True, months=1),
            admin,
            db,
        )
    )

    assert grant["active"] is True
    assert db.query(Subscription).count() == 1
    assert active_subscription(db, user)
    payment_state = asyncio.run(current_payment(user, db, Settings()))
    assert payment_state["member_active"] is True
    assert db.query(ManualPayment).count() == 0

    revoke = asyncio.run(
        admin_update_membership(
            user.id,
            MembershipRequest(active=False),
            admin,
            db,
        )
    )

    assert revoke["active"] is False
    assert active_subscription(db, user) is None
