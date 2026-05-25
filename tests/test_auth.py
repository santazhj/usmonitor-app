import asyncio
from urllib.parse import parse_qs, urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.main import AuthRequest, active_subscription, request_login, verify_login
from app.models import Base, Subscription, User
from app.security import sign_payload, verify_payload


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_request_login_allows_new_email_without_invite():
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")

    result = asyncio.run(
        request_login(AuthRequest(email="NEW@example.com"), settings=settings)
    )

    token = parse_qs(urlparse(result["dev_magic_link"]).query)["token"][0]
    payload = verify_payload(token, settings.secret_key)
    assert result["ok"] is True
    assert payload["email"] == "new@example.com"
    assert "invite_code" not in payload


def test_verify_login_creates_free_user_without_subscription():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")
    token = sign_payload(
        {"typ": "magic", "email": "friend@example.com"},
        settings.secret_key,
        60,
    )

    response = asyncio.run(verify_login(token, db=db, settings=settings))

    user = db.query(User).filter(User.email == "friend@example.com").one()
    assert response.status_code == 302
    assert "serenity_session=" in response.headers["set-cookie"]
    assert user.status == "active"
    assert user.is_admin is False
    assert db.query(Subscription).count() == 0
    assert active_subscription(db, user) is None
