from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db, init_db
from app.jobs.poll_sources import poll_sources
from app.models import (
    AlertSummary,
    Delivery,
    JobRun,
    ManualPayment,
    MonitorList,
    MonitoredSource,
    PushSubscription,
    Subscription,
    User,
    utcnow,
)
from app.security import sign_payload, verify_payload
from app.services.emailer import send_magic_link
from app.services.dashboard import dashboard_tickers, get_dashboard_snapshot
from app.services.market_data import fetch_massive_market_data
from app.services.payments import confirm_payment, get_or_create_pending_payment
from app.services.push import send_push
from app.services.seed import seed_defaults

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
SESSION_COOKIE = "serenity_session"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = next(get_db())
    try:
        seed_defaults(db, get_settings())
    finally:
        db.close()
    yield


app = FastAPI(title="Serenity Alerts", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AuthRequest(BaseModel):
    email: str


class PushSubscribeRequest(BaseModel):
    subscription: dict


class ConfirmPaymentRequest(BaseModel):
    tx_hash: str = ""
    months: int = 1


class RejectPaymentRequest(BaseModel):
    reason: str = ""


def clean_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or len(email) > 320:
        raise HTTPException(status_code=400, detail="Invalid email")
    return email


def current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    payload = verify_payload(token or "", settings.secret_key)
    if not payload or payload.get("typ") != "session":
        raise HTTPException(status_code=401, detail="Not signed in")
    user = db.query(User).filter(User.id == payload.get("uid")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user


def current_admin(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def active_subscription(db: Session, user: User, monitor_list_id: str | None = None):
    if user.is_admin:
        return True
    query = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
        Subscription.expires_at > utcnow(),
    )
    if monitor_list_id:
        query = query.filter(Subscription.monitor_list_id == monitor_list_id)
    return query.order_by(Subscription.expires_at.desc()).first()


def accessible_monitor_list_ids(db: Session, user: User) -> list[str]:
    if user.is_admin:
        return [
            item.id
            for item in db.query(MonitorList)
            .filter(MonitorList.is_active.is_(True))
            .all()
        ]
    subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.expires_at > utcnow(),
        )
        .all()
    )
    return [item.monitor_list_id for item in subscriptions]


def serialize_summary(summary: AlertSummary) -> dict:
    return {
        "id": summary.id,
        "title": summary.title,
        "notification_text": summary.notification_text,
        "bullets": summary.bullets,
        "tickers": summary.tickers,
        "why_it_matters": summary.why_it_matters,
        "risks": summary.risks,
        "source_url": summary.source_url,
        "model": summary.model,
        "created_at": summary.created_at.isoformat(),
        "disclaimer": "仅为情报摘要，不构成投资建议、收益承诺或个性化交易方案。",
    }


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin")
async def admin_page():
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest")


@app.get("/sw.js")
async def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/icon.svg")
async def icon():
    return FileResponse(STATIC_DIR / "icon.svg", media_type="image/svg+xml")


@app.post("/api/auth/request")
async def request_login(
    payload: AuthRequest,
    settings: Settings = Depends(get_settings),
):
    email = clean_email(payload.email)
    token = sign_payload(
        {"typ": "magic", "email": email},
        settings.secret_key,
        settings.magic_link_ttl_seconds,
    )
    link = f"{settings.base_url}/auth/verify?token={quote(token)}"
    result = await send_magic_link(settings, email, link)
    return {"ok": True, **result}


@app.get("/auth/verify")
async def verify_login(
    token: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = verify_payload(token, settings.secret_key)
    if not payload or payload.get("typ") != "magic":
        raise HTTPException(status_code=400, detail="Login link is invalid or expired")

    email = clean_email(payload["email"])
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, is_admin=email in settings.admin_emails)
        db.add(user)
    elif email in settings.admin_emails and not user.is_admin:
        user.is_admin = True

    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)

    session_token = sign_payload(
        {"typ": "session", "uid": user.id},
        settings.secret_key,
        settings.session_ttl_seconds,
    )
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return response


@app.post("/api/auth/logout")
async def logout():
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/api/config")
async def public_config(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "vapid_public_key": settings.vapid_public_key,
        "monthly_price_usdt": settings.monthly_price_usdt,
        "usdt_trc20_address": settings.usdt_trc20_address,
        "usdt_erc20_address": settings.usdt_erc20_address,
        "base_url": settings.base_url,
    }


@app.get("/api/dashboard")
async def dashboard(settings: Settings = Depends(get_settings)):
    market_data = await fetch_massive_market_data(settings, dashboard_tickers())
    return get_dashboard_snapshot(market_data)


@app.get("/api/me")
async def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    subscription = active_subscription(db, user)
    return {
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
        "subscription": {
            "active": bool(subscription),
            "expires_at": subscription.expires_at.isoformat()
            if subscription is not True and subscription
            else None,
        },
    }


@app.get("/api/lists")
async def lists(user: User = Depends(current_user), db: Session = Depends(get_db)):
    monitor_lists = (
        db.query(MonitorList).filter(MonitorList.is_active.is_(True)).all()
    )
    return [
        {
            "id": item.id,
            "slug": item.slug,
            "name": item.name,
            "description": item.description,
            "subscription_active": bool(active_subscription(db, user, item.id)),
        }
        for item in monitor_lists
    ]


@app.get("/api/payments/current")
async def current_payment(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if user.is_admin:
        return {
            "admin_bypass": True,
            "amount_usdt": settings.monthly_price_usdt,
            "trc20_address": settings.usdt_trc20_address,
            "erc20_address": settings.usdt_erc20_address,
            "status": "admin",
        }
    payment = get_or_create_pending_payment(db, settings, user)
    return {
        "id": payment.id,
        "amount_usdt": payment.amount_usdt,
        "chain": payment.chain,
        "payment_code": payment.payment_code,
        "status": payment.status,
        "trc20_address": settings.usdt_trc20_address,
        "erc20_address": settings.usdt_erc20_address,
        "created_at": payment.created_at.isoformat(),
    }


@app.get("/api/feed")
async def feed(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    limit: int = 30,
):
    list_ids = accessible_monitor_list_ids(db, user)
    if not list_ids:
        return []
    summaries = (
        db.query(AlertSummary)
        .filter(AlertSummary.monitor_list_id.in_(list_ids))
        .order_by(AlertSummary.created_at.desc())
        .limit(min(max(limit, 1), 100))
        .all()
    )
    return [serialize_summary(summary) for summary in summaries]


@app.post("/api/push/subscribe")
async def subscribe_push(
    payload: PushSubscribeRequest,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    subscription = payload.subscription
    endpoint = subscription.get("endpoint", "")
    keys = subscription.get("keys", {})
    if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
        raise HTTPException(status_code=400, detail="Invalid push subscription")

    existing = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == endpoint)
        .one_or_none()
    )
    if existing:
        existing.user_id = user.id
        existing.p256dh = keys["p256dh"]
        existing.auth = keys["auth"]
        existing.is_active = True
        existing.disabled_at = None
        existing.user_agent = request.headers.get("user-agent", "")
    else:
        db.add(
            PushSubscription(
                user_id=user.id,
                endpoint=endpoint,
                p256dh=keys["p256dh"],
                auth=keys["auth"],
                user_agent=request.headers.get("user-agent", ""),
            )
        )
    db.commit()
    return {"ok": True}


@app.post("/api/push/test")
async def test_push(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    pushes = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user.id, PushSubscription.is_active.is_(True))
        .all()
    )
    sent = 0
    failed = 0
    for push in pushes:
        ok, error = send_push(
            settings,
            push,
            {
                "title": "Serenity Alerts",
                "body": "测试推送已送达。仅为系统测试，不构成投资建议。",
                "url": "/",
            },
        )
        if ok:
            sent += 1
            push.last_success_at = utcnow()
        else:
            failed += 1
            if "410" in error or "404" in error:
                push.is_active = False
                push.disabled_at = utcnow()
    db.commit()
    return {"sent": sent, "failed": failed}


@app.get("/api/admin/overview")
async def admin_overview(
    _: User = Depends(current_admin), db: Session = Depends(get_db)
):
    pending_payments = (
        db.query(ManualPayment)
        .filter(ManualPayment.status == "pending")
        .order_by(ManualPayment.created_at.desc())
        .limit(50)
        .all()
    )
    users = db.query(User).order_by(User.created_at.desc()).limit(50).all()
    sources = db.query(MonitoredSource).order_by(MonitoredSource.created_at.desc()).all()
    jobs = db.query(JobRun).order_by(JobRun.started_at.desc()).limit(20).all()
    return {
        "counts": {
            "users": db.query(func.count(User.id)).scalar(),
            "push_subscriptions": db.query(func.count(PushSubscription.id)).scalar(),
            "summaries": db.query(func.count(AlertSummary.id)).scalar(),
            "deliveries": db.query(func.count(Delivery.id)).scalar(),
        },
        "pending_payments": [
            {
                "id": item.id,
                "email": item.user.email,
                "amount_usdt": item.amount_usdt,
                "payment_code": item.payment_code,
                "created_at": item.created_at.isoformat(),
            }
            for item in pending_payments
        ],
        "users": [
            {
                "id": item.id,
                "email": item.email,
                "is_admin": item.is_admin,
                "created_at": item.created_at.isoformat(),
                "last_login_at": item.last_login_at.isoformat()
                if item.last_login_at
                else None,
            }
            for item in users
        ],
        "sources": [
            {
                "id": item.id,
                "handle": item.handle,
                "external_id": item.external_id,
                "last_seen_post_id": item.last_seen_post_id,
                "is_active": item.is_active,
            }
            for item in sources
        ],
        "jobs": [
            {
                "id": item.id,
                "job_name": item.job_name,
                "status": item.status,
                "message": item.message,
                "metadata": item.metadata_json,
                "started_at": item.started_at.isoformat(),
                "finished_at": item.finished_at.isoformat()
                if item.finished_at
                else None,
            }
            for item in jobs
        ],
    }


@app.post("/api/admin/payments/{payment_id}/confirm")
async def admin_confirm_payment(
    payment_id: str,
    payload: ConfirmPaymentRequest,
    _: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    payment = db.query(ManualPayment).filter(ManualPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    subscription = confirm_payment(db, payment, payload.tx_hash, payload.months)
    return {"ok": True, "expires_at": subscription.expires_at.isoformat()}


@app.post("/api/admin/payments/{payment_id}/reject")
async def admin_reject_payment(
    payment_id: str,
    payload: RejectPaymentRequest,
    _: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    payment = db.query(ManualPayment).filter(ManualPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment.status = "rejected"
    payment.tx_hash = payload.reason
    db.commit()
    return {"ok": True}


@app.post("/api/admin/poll")
async def admin_poll(_: User = Depends(current_admin), db: Session = Depends(get_db)):
    result = await poll_sources(db)
    return result


@app.post("/api/jobs/poll")
async def job_poll(
    secret: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.job_secret or secret != settings.job_secret:
        raise HTTPException(status_code=403, detail="Invalid job secret")
    return await poll_sources(db)
