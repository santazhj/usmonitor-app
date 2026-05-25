from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def uuid_str() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="user")
    push_subscriptions: Mapped[list[PushSubscription]] = relationship(
        back_populates="user"
    )


class InviteCode(Base):
    __tablename__ = "invite_codes"

    code: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(160), default="")
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    uses_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def usable(self) -> bool:
        now = utcnow()
        if self.disabled_at:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return self.uses_count < self.max_uses


class MonitorList(Base):
    __tablename__ = "monitor_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    sources: Mapped[list[MonitoredSource]] = relationship(back_populates="monitor_list")
    summaries: Mapped[list[AlertSummary]] = relationship(back_populates="monitor_list")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    monitor_list_id: Mapped[str] = mapped_column(ForeignKey("monitor_lists.id"))
    status: Mapped[str] = mapped_column(String(32), default="active")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="subscriptions")
    monitor_list: Mapped[MonitorList] = relationship()


class ManualPayment(Base):
    __tablename__ = "manual_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    amount_usdt: Mapped[int] = mapped_column(Integer, default=99)
    chain: Mapped[str] = mapped_column(String(32), default="TRC20+ERC20")
    payment_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    receiving_address: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    tx_hash: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship()


class MonitoredSource(Base):
    __tablename__ = "monitored_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    monitor_list_id: Mapped[str] = mapped_column(ForeignKey("monitor_lists.id"))
    source_type: Mapped[str] = mapped_column(String(32), default="x_user")
    handle: Mapped[str] = mapped_column(String(80), index=True)
    external_id: Mapped[str] = mapped_column(String(80), default="")
    last_seen_post_id: Mapped[str] = mapped_column(String(80), default="")
    poll_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    monitor_list: Mapped[MonitorList] = relationship(back_populates="sources")
    posts: Mapped[list[XPost]] = relationship(back_populates="source")


class XPost(Base):
    __tablename__ = "x_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tweet_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("monitored_sources.id"))
    author_handle: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    created_at_x: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    url: Mapped[str] = mapped_column(Text)
    raw_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source: Mapped[MonitoredSource] = relationship(back_populates="posts")
    summary: Mapped[AlertSummary] = relationship(back_populates="post")


class AlertSummary(Base):
    __tablename__ = "alert_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    post_id: Mapped[str] = mapped_column(ForeignKey("x_posts.id"), unique=True)
    monitor_list_id: Mapped[str] = mapped_column(ForeignKey("monitor_lists.id"))
    title: Mapped[str] = mapped_column(String(200))
    notification_text: Mapped[str] = mapped_column(String(220))
    bullets: Mapped[list[str]] = mapped_column(JSON, default=list)
    tickers: Mapped[list[str]] = mapped_column(JSON, default=list)
    why_it_matters: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_url: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    post: Mapped[XPost] = relationship(back_populates="summary")
    monitor_list: Mapped[MonitorList] = relationship(back_populates="summaries")
    deliveries: Mapped[list[Delivery]] = relationship(back_populates="summary")


class WatchlistMention(Base):
    __tablename__ = "watchlist_mentions"
    __table_args__ = (
        UniqueConstraint("summary_id", "ticker", name="uq_watchlist_summary_ticker"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    company: Mapped[str] = mapped_column(String(200), default="")
    sentiment: Mapped[str] = mapped_column(String(32), default="positive", index=True)
    reason: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str] = mapped_column(Text, default="")
    post_id: Mapped[str | None] = mapped_column(ForeignKey("x_posts.id"), index=True)
    summary_id: Mapped[str | None] = mapped_column(
        ForeignKey("alert_summaries.id"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    post: Mapped[XPost | None] = relationship()
    summary: Mapped[AlertSummary | None] = relationship()


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    __table_args__ = (UniqueConstraint("endpoint", name="uq_push_endpoint"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    endpoint: Mapped[str] = mapped_column(Text)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)
    user_agent: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="push_subscriptions")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    visitor_id: Mapped[str] = mapped_column(String(120), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    path: Mapped[str] = mapped_column(String(500), default="/", index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str] = mapped_column(String(16), default="")
    viewport: Mapped[str] = mapped_column(String(32), default="")
    user_agent: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User | None] = relationship()


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    summary_id: Mapped[str] = mapped_column(ForeignKey("alert_summaries.id"), index=True)
    push_subscription_id: Mapped[str] = mapped_column(
        ForeignKey("push_subscriptions.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    summary: Mapped[AlertSummary] = relationship(back_populates="deliveries")
    push_subscription: Mapped[PushSubscription] = relationship()


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    job_name: Mapped[str] = mapped_column(String(120), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running")
    message: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
