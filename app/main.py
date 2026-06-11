from __future__ import annotations

import hashlib
import hmac
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote, urlparse

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
    AnalyticsEvent,
    Delivery,
    JobRun,
    ManualPayment,
    MonitorList,
    MonitoredSource,
    PushSubscription,
    Subscription,
    User,
    WatchlistMention,
    utcnow,
)
from app.security import sign_payload, verify_payload
from app.services.emailer import send_login_code, send_magic_link
from app.services.dashboard import (
    dashboard_tickers,
    get_dashboard_snapshot,
    mention_rows,
)
from app.services.feed_localization import localize_feed_for_zh
from app.services.market_data import fetch_dashboard_market_data
from app.services.options_analysis import build_options_payload, options_progress_snapshot, search_option_tickers
from app.services.payments import confirm_payment, get_or_create_pending_payment
from app.services.push import send_push
from app.services.seed import seed_defaults

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
SESSION_COOKIE = "serenity_session"
PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 210_000
PASSWORD_MIN_LENGTH = 8
AUTH_CODE_PURPOSES = {"login", "register", "reset"}


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


def session_cookie_domain(settings: Settings) -> str | None:
    if settings.cookie_domain:
        return settings.cookie_domain
    host = urlparse(settings.base_url).hostname or ""
    if host == "usmonitor.app" or host.endswith(".usmonitor.app"):
        return ".usmonitor.app"
    return None


def set_session_cookie(response: Response, settings: Settings, session_token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
        domain=session_cookie_domain(settings),
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        secure=settings.secure_cookies,
        samesite="lax",
        domain=session_cookie_domain(settings),
        path="/",
    )


class AuthRequest(BaseModel):
    email: str


class AuthCodeRequest(BaseModel):
    email: str
    purpose: str = "login"


class AuthCodeVerifyRequest(BaseModel):
    email: str
    code: str
    challenge_token: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    code: str
    challenge_token: str


class PasswordLoginRequest(BaseModel):
    email: str
    password: str


class PasswordResetRequest(BaseModel):
    email: str
    password: str
    code: str
    challenge_token: str


class PushSubscribeRequest(BaseModel):
    subscription: dict


class ConfirmPaymentRequest(BaseModel):
    tx_hash: str = ""
    months: int = 1


class RejectPaymentRequest(BaseModel):
    reason: str = ""


class AnalyticsEventRequest(BaseModel):
    visitor_id: str
    event_type: str = "pageview"
    path: str = "/"
    duration_seconds: int = 0
    language: str = ""
    viewport: str = ""


class MembershipRequest(BaseModel):
    active: bool
    months: int = 1


def clean_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or len(email) > 320:
        raise HTTPException(status_code=400, detail="Invalid email")
    return email


def login_code_hash(settings: Settings, email: str, code: str, salt: str) -> str:
    return hmac.new(
        settings.secret_key.encode(),
        f"{email}:{code}:{salt}".encode(),
        hashlib.sha256,
    ).hexdigest()


def clean_code_purpose(value: str) -> str:
    purpose = value.strip().lower()
    if purpose not in AUTH_CODE_PURPOSES:
        raise HTTPException(status_code=400, detail="Invalid verification purpose")
    return purpose


def clean_password(password: str) -> str:
    password = password or ""
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {PASSWORD_MIN_LENGTH} characters",
        )
    return password


def password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PASSWORD_HASH_ITERATIONS,
    ).hex()
    return f"{PASSWORD_HASH_ALGORITHM}${PASSWORD_HASH_ITERATIONS}${salt}${digest}"


def password_matches(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        if algorithm != PASSWORD_HASH_ALGORITHM:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            int(iterations),
        ).hex()
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(digest, expected)


def verify_email_code_challenge(
    settings: Settings,
    email: str,
    code: str,
    challenge_token: str,
    purpose: str,
) -> None:
    cleaned_code = code.strip().replace(" ", "")
    challenge = verify_payload(challenge_token, settings.secret_key)
    challenge_purpose = str(challenge.get("purpose", "login")) if challenge else ""
    if (
        not challenge
        or challenge.get("typ") != "email_code"
        or challenge.get("email") != email
        or challenge_purpose != purpose
        or not hmac.compare_digest(
            str(challenge.get("code_hash", "")),
            login_code_hash(
                settings,
                email,
                cleaned_code,
                str(challenge.get("salt", "")),
            ),
        )
    ):
        raise HTTPException(
            status_code=400, detail="Verification code is invalid or expired"
        )


def serialize_user_session(db: Session, user: User) -> dict:
    subscription = active_subscription(db, user)
    return {
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
        "has_password": bool(user.password_hash),
        "subscription": {
            "active": bool(subscription),
            "expires_at": subscription.expires_at.isoformat()
            if subscription is not True and subscription
            else None,
        },
    }


def get_or_create_user(db: Session, settings: Settings, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, is_admin=email in settings.admin_emails)
        db.add(user)
    elif email in settings.admin_emails and not user.is_admin:
        user.is_admin = True
    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)
    return user


def create_session_for_user(
    response: Response,
    settings: Settings,
    user: User,
) -> None:
    session_token = sign_payload(
        {"typ": "session", "uid": user.id},
        settings.secret_key,
        settings.session_ttl_seconds,
    )
    set_session_cookie(response, settings, session_token)


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


def optional_current_user(
    request: Request,
    db: Session,
    settings: Settings,
) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)
    payload = verify_payload(token or "", settings.secret_key)
    if not payload or payload.get("typ") != "session":
        return None
    return db.query(User).filter(User.id == payload.get("uid")).first()


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


def grant_membership(db: Session, user: User, months: int = 1) -> Subscription:
    monitor_list = db.query(MonitorList).filter(MonitorList.is_active.is_(True)).first()
    if not monitor_list:
        raise HTTPException(status_code=400, detail="No active monitor list exists")

    now = utcnow()
    current = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.monitor_list_id == monitor_list.id,
            Subscription.status == "active",
        )
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    start = max(now, current.expires_at) if current else now
    subscription = Subscription(
        user_id=user.id,
        monitor_list_id=monitor_list.id,
        starts_at=start,
        expires_at=start + timedelta(days=31 * max(1, min(months, 24))),
        status="active",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def revoke_membership(db: Session, user: User) -> None:
    now = utcnow()
    subscriptions = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.expires_at > now,
        )
        .all()
    )
    for subscription in subscriptions:
        subscription.status = "canceled"
        subscription.expires_at = now
    db.commit()


def serialize_summary(summary: AlertSummary, localized: dict | None = None) -> dict:
    localized = localized or {}
    return {
        "id": summary.id,
        "title": localized.get("title") or summary.title,
        "notification_text": localized.get("notification_text") or summary.notification_text,
        "bullets": localized.get("bullets") or summary.bullets,
        "tickers": summary.tickers,
        "why_it_matters": localized.get("why_it_matters") or summary.why_it_matters,
        "risks": summary.risks,
        "source_url": summary.source_url,
        "model": summary.model,
        "created_at": summary.created_at.isoformat(),
        "disclaimer": "仅为情报摘要，不构成投资建议、收益承诺或个性化交易方案。",
    }


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login")
async def login_page():
    return FileResponse(STATIC_DIR / "login.html")


@app.get("/options")
async def options_page():
    return FileResponse(STATIC_DIR / "options.html")


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


@app.post("/api/auth/code/request")
async def request_login_code(
    payload: AuthCodeRequest,
    settings: Settings = Depends(get_settings),
):
    email = clean_email(payload.email)
    purpose = clean_code_purpose(payload.purpose)
    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_urlsafe(12)
    challenge_token = sign_payload(
        {
            "typ": "email_code",
            "email": email,
            "purpose": purpose,
            "salt": salt,
            "code_hash": login_code_hash(settings, email, code, salt),
        },
        settings.secret_key,
        settings.magic_link_ttl_seconds,
    )
    result = await send_login_code(settings, email, code, purpose=purpose)
    return {"ok": True, "challenge_token": challenge_token, **result}


@app.post("/api/auth/code/verify")
async def verify_login_code(
    payload: AuthCodeVerifyRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    email = clean_email(payload.email)
    verify_email_code_challenge(
        settings, email, payload.code, payload.challenge_token, "login"
    )

    user = get_or_create_user(db, settings, email)
    create_session_for_user(response, settings, user)
    return {"ok": True, "user": serialize_user_session(db, user)}


@app.post("/api/auth/register")
async def register_account(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    email = clean_email(payload.email)
    password = clean_password(payload.password)
    verify_email_code_challenge(
        settings, email, payload.code, payload.challenge_token, "register"
    )
    user = db.query(User).filter(User.email == email).first()
    if user and user.password_hash:
        raise HTTPException(status_code=409, detail="Account already has a password")
    if not user:
        user = User(email=email, is_admin=email in settings.admin_emails)
        db.add(user)
    elif email in settings.admin_emails and not user.is_admin:
        user.is_admin = True
    user.password_hash = password_hash(password)
    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)
    create_session_for_user(response, settings, user)
    return {"ok": True, "user": serialize_user_session(db, user)}


@app.post("/api/auth/login")
async def password_login(
    payload: PasswordLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    email = clean_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not password_matches(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if email in settings.admin_emails and not user.is_admin:
        user.is_admin = True
    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)
    create_session_for_user(response, settings, user)
    return {"ok": True, "user": serialize_user_session(db, user)}


@app.post("/api/auth/password/reset")
async def reset_password(
    payload: PasswordResetRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    email = clean_email(payload.email)
    password = clean_password(payload.password)
    verify_email_code_challenge(
        settings, email, payload.code, payload.challenge_token, "reset"
    )
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    user.password_hash = password_hash(password)
    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)
    create_session_for_user(response, settings, user)
    return {"ok": True, "user": serialize_user_session(db, user)}


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
    user = get_or_create_user(db, settings, email)

    session_token = sign_payload(
        {"typ": "session", "uid": user.id},
        settings.secret_key,
        settings.session_ttl_seconds,
    )
    response = RedirectResponse(url="/", status_code=302)
    set_session_cookie(response, settings, session_token)
    return response


@app.post("/api/auth/logout")
async def logout(settings: Settings = Depends(get_settings)):
    response = Response(status_code=204)
    clear_session_cookie(response, settings)
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
async def dashboard(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    mentions = (
        db.query(WatchlistMention)
        .filter(
            WatchlistMention.is_active.is_(True),
            WatchlistMention.sentiment == "positive",
        )
        .order_by(WatchlistMention.created_at.desc())
        .limit(100)
        .all()
    )
    dynamic_rows = mention_rows(mentions)
    tickers = dashboard_tickers() + [item["ticker"] for item in dynamic_rows]
    market_data = await fetch_dashboard_market_data(settings, tickers)
    return get_dashboard_snapshot(market_data, dynamic_rows, mentions)


@app.get("/api/options/scan")
async def options_scan(
    tickers: str = "",
    mode: str = "quick",
    source: str = "",
    allowInitialFull: bool = False,
    settings: Settings = Depends(get_settings),
):
    return await build_options_payload(settings, tickers, mode, allow_initial_full=allowInitialFull, source=source)


@app.get("/api/options/progress")
async def options_progress(
    tickers: str = "",
    source: str = "",
    settings: Settings = Depends(get_settings),
):
    return options_progress_snapshot(settings, tickers, source=source)


@app.get("/api/options/tickers")
async def options_ticker_search(
    q: str = "",
    settings: Settings = Depends(get_settings),
):
    return {"results": await search_option_tickers(settings, q)}


@app.post("/api/analytics/event")
async def analytics_event(
    payload: AnalyticsEventRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    event_type = payload.event_type.strip().lower()
    if event_type not in {"pageview", "heartbeat"}:
        raise HTTPException(status_code=400, detail="Invalid analytics event")

    visitor_id = payload.visitor_id.strip()[:120]
    if len(visitor_id) < 8:
        raise HTTPException(status_code=400, detail="Invalid visitor id")

    user = optional_current_user(request, db, settings)
    event = AnalyticsEvent(
        user_id=user.id if user else None,
        visitor_id=visitor_id,
        event_type=event_type,
        path=(payload.path or "/")[:500],
        duration_seconds=max(0, min(int(payload.duration_seconds or 0), 1800)),
        language=payload.language[:16],
        viewport=payload.viewport[:32],
        user_agent=request.headers.get("user-agent", "")[:1000],
    )
    db.add(event)
    db.commit()
    return {"ok": True}


@app.get("/api/me")
async def me(
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    session_token = sign_payload(
        {"typ": "session", "uid": user.id},
        settings.secret_key,
        settings.session_ttl_seconds,
    )
    set_session_cookie(response, settings, session_token)
    return serialize_user_session(db, user)


@app.get("/api/lists")
async def lists(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = optional_current_user(request, db, settings)
    monitor_lists = (
        db.query(MonitorList).filter(MonitorList.is_active.is_(True)).all()
    )
    return [
        {
            "id": item.id,
            "slug": item.slug,
            "name": item.name,
            "description": item.description,
            "public_access": True,
            "subscription_active": bool(active_subscription(db, user, item.id))
            if user
            else False,
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
    subscription = active_subscription(db, user)
    if subscription:
        return {
            "member_active": True,
            "amount_usdt": settings.monthly_price_usdt,
            "trc20_address": settings.usdt_trc20_address,
            "erc20_address": settings.usdt_erc20_address,
            "status": "active",
            "expires_at": subscription.expires_at.isoformat(),
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
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    limit: int = 30,
    lang: str = "en",
):
    list_ids = [
        item.id
        for item in db.query(MonitorList)
        .filter(MonitorList.is_active.is_(True))
        .all()
    ]
    if not list_ids:
        return []
    summaries = (
        db.query(AlertSummary)
        .filter(AlertSummary.monitor_list_id.in_(list_ids))
        .order_by(AlertSummary.created_at.desc())
        .limit(min(max(limit, 1), 100))
        .all()
    )
    localized = (
        localize_feed_for_zh(settings, db, summaries)
        if lang.lower().startswith("zh")
        else {}
    )
    return [serialize_summary(summary, localized.get(summary.id)) for summary in summaries]


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
    now = utcnow()
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
    total_page_views = (
        db.query(func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.event_type == "pageview")
        .scalar()
        or 0
    )
    total_duration_seconds = (
        db.query(func.coalesce(func.sum(AnalyticsEvent.duration_seconds), 0)).scalar()
        or 0
    )
    active_members = (
        db.query(func.count(func.distinct(Subscription.user_id)))
        .filter(Subscription.status == "active", Subscription.expires_at > now)
        .scalar()
        or 0
    )
    page_view_rows = (
        db.query(AnalyticsEvent.path, func.count(AnalyticsEvent.id))
        .filter(AnalyticsEvent.event_type == "pageview")
        .group_by(AnalyticsEvent.path)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(20)
        .all()
    )
    page_duration_rows = (
        db.query(
            AnalyticsEvent.path,
            func.coalesce(func.sum(AnalyticsEvent.duration_seconds), 0),
        )
        .group_by(AnalyticsEvent.path)
        .all()
    )
    page_seconds = {path: int(seconds or 0) for path, seconds in page_duration_rows}

    user_stats = {}
    for item in users:
        views = (
            db.query(func.count(AnalyticsEvent.id))
            .filter(
                AnalyticsEvent.user_id == item.id,
                AnalyticsEvent.event_type == "pageview",
            )
            .scalar()
            or 0
        )
        seconds = (
            db.query(func.coalesce(func.sum(AnalyticsEvent.duration_seconds), 0))
            .filter(AnalyticsEvent.user_id == item.id)
            .scalar()
            or 0
        )
        last_seen = (
            db.query(func.max(AnalyticsEvent.created_at))
            .filter(AnalyticsEvent.user_id == item.id)
            .scalar()
        )
        subscription = active_subscription(db, item)
        user_stats[item.id] = {
            "page_views": int(views),
            "total_seconds": int(seconds or 0),
            "last_seen_at": last_seen.isoformat() if last_seen else None,
            "subscription_active": bool(subscription),
            "subscription_expires_at": subscription.expires_at.isoformat()
            if subscription is not True and subscription
            else None,
        }

    return {
        "counts": {
            "users": db.query(func.count(User.id)).scalar(),
            "active_members": active_members,
            "page_views": total_page_views,
            "avg_stay_seconds": round(
                total_duration_seconds / max(total_page_views, 1)
            ),
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
                **user_stats[item.id],
            }
            for item in users
        ],
        "page_stats": [
            {
                "path": path,
                "page_views": int(views or 0),
                "total_seconds": page_seconds.get(path, 0),
            }
            for path, views in page_view_rows
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


@app.post("/api/admin/users/{user_id}/membership")
async def admin_update_membership(
    user_id: str,
    payload: MembershipRequest,
    _: User = Depends(current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_admin:
        return {"ok": True, "active": True, "expires_at": None, "admin_bypass": True}

    if payload.active:
        subscription = grant_membership(db, user, payload.months)
        return {
            "ok": True,
            "active": True,
            "expires_at": subscription.expires_at.isoformat(),
        }

    revoke_membership(db, user)
    return {"ok": True, "active": False, "expires_at": None}


@app.post("/api/jobs/poll")
async def job_poll(
    secret: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.job_secret or secret != settings.job_secret:
        raise HTTPException(status_code=403, detail="Invalid job secret")
    return await poll_sources(db)
