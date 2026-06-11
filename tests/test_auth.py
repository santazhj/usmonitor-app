import asyncio
from urllib.parse import parse_qs, urlparse

from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.main import (
    AuthCodeRequest,
    AuthCodeVerifyRequest,
    AuthRequest,
    PasswordLoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    active_subscription,
    me,
    password_login,
    register_account,
    reset_password,
    request_login_code,
    request_login,
    session_cookie_domain,
    verify_login_code,
    verify_login,
)
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


def test_code_login_creates_or_signs_in_free_user():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")

    code_response = asyncio.run(
        request_login_code(AuthCodeRequest(email="Friend@example.com"), settings=settings)
    )
    response = Response()
    result = asyncio.run(
        verify_login_code(
            AuthCodeVerifyRequest(
                email="friend@example.com",
                code=code_response["dev_code"],
                challenge_token=code_response["challenge_token"],
            ),
            response=response,
            db=db,
            settings=settings,
        )
    )

    user = db.query(User).filter(User.email == "friend@example.com").one()
    assert result["ok"] is True
    assert result["user"]["email"] == "friend@example.com"
    assert "serenity_session=" in response.headers["set-cookie"]
    assert user.status == "active"
    assert db.query(Subscription).count() == 0


def test_code_login_rejects_wrong_code():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")

    code_response = asyncio.run(
        request_login_code(AuthCodeRequest(email="friend@example.com"), settings=settings)
    )
    wrong_code = "000000" if code_response["dev_code"] != "000000" else "111111"

    try:
        asyncio.run(
            verify_login_code(
                AuthCodeVerifyRequest(
                    email="friend@example.com",
                    code=wrong_code,
                    challenge_token=code_response["challenge_token"],
                ),
                response=Response(),
                db=db,
                settings=settings,
            )
        )
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("Wrong code should be rejected")

    assert db.query(User).count() == 0


def test_register_sets_password_and_session_cookie():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")
    code_response = asyncio.run(
        request_login_code(
            AuthCodeRequest(email="Friend@example.com", purpose="register"),
            settings=settings,
        )
    )
    response = Response()

    result = asyncio.run(
        register_account(
            RegisterRequest(
                email="friend@example.com",
                password="strong-password",
                code=code_response["dev_code"],
                challenge_token=code_response["challenge_token"],
            ),
            response=response,
            db=db,
            settings=settings,
        )
    )

    user = db.query(User).filter(User.email == "friend@example.com").one()
    assert result["ok"] is True
    assert result["user"]["has_password"] is True
    assert user.password_hash.startswith("pbkdf2_sha256$")
    assert "serenity_session=" in response.headers["set-cookie"]


def test_password_login_uses_existing_password():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")
    code_response = asyncio.run(
        request_login_code(
            AuthCodeRequest(email="friend@example.com", purpose="register"),
            settings=settings,
        )
    )
    asyncio.run(
        register_account(
            RegisterRequest(
                email="friend@example.com",
                password="strong-password",
                code=code_response["dev_code"],
                challenge_token=code_response["challenge_token"],
            ),
            response=Response(),
            db=db,
            settings=settings,
        )
    )

    response = Response()
    result = asyncio.run(
        password_login(
            PasswordLoginRequest(email="friend@example.com", password="strong-password"),
            response=response,
            db=db,
            settings=settings,
        )
    )

    assert result["user"]["email"] == "friend@example.com"
    assert "serenity_session=" in response.headers["set-cookie"]


def test_password_login_rejects_wrong_password():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")
    db.add(User(email="friend@example.com", password_hash="bad-hash"))
    db.commit()

    try:
        asyncio.run(
            password_login(
                PasswordLoginRequest(email="friend@example.com", password="wrong-password"),
                response=Response(),
                db=db,
                settings=settings,
            )
        )
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 401
    else:
        raise AssertionError("Wrong password should be rejected")


def test_reset_password_with_email_code_updates_password():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")
    register_code = asyncio.run(
        request_login_code(
            AuthCodeRequest(email="friend@example.com", purpose="register"),
            settings=settings,
        )
    )
    asyncio.run(
        register_account(
            RegisterRequest(
                email="friend@example.com",
                password="old-password",
                code=register_code["dev_code"],
                challenge_token=register_code["challenge_token"],
            ),
            response=Response(),
            db=db,
            settings=settings,
        )
    )
    reset_code = asyncio.run(
        request_login_code(
            AuthCodeRequest(email="friend@example.com", purpose="reset"),
            settings=settings,
        )
    )
    response = Response()

    result = asyncio.run(
        reset_password(
            PasswordResetRequest(
                email="friend@example.com",
                password="new-password",
                code=reset_code["dev_code"],
                challenge_token=reset_code["challenge_token"],
            ),
            response=response,
            db=db,
            settings=settings,
        )
    )

    assert result["user"]["has_password"] is True
    assert "serenity_session=" in response.headers["set-cookie"]
    login_response = Response()
    login_result = asyncio.run(
        password_login(
            PasswordLoginRequest(email="friend@example.com", password="new-password"),
            response=login_response,
            db=db,
            settings=settings,
        )
    )
    assert login_result["user"]["email"] == "friend@example.com"


def test_register_rejects_login_purpose_code():
    db = make_session()
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")
    code_response = asyncio.run(
        request_login_code(AuthCodeRequest(email="friend@example.com"), settings=settings)
    )

    try:
        asyncio.run(
            register_account(
                RegisterRequest(
                    email="friend@example.com",
                    password="strong-password",
                    code=code_response["dev_code"],
                    challenge_token=code_response["challenge_token"],
                ),
                response=Response(),
                db=db,
                settings=settings,
            )
        )
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 400
    else:
        raise AssertionError("Login-purpose code should not register accounts")


def test_verify_login_sets_persistent_cross_subdomain_cookie_for_production():
    db = make_session()
    settings = Settings(base_url="https://usmonitor.app", secret_key="test-secret")
    token = sign_payload(
        {"typ": "magic", "email": "owner@example.com"},
        settings.secret_key,
        60,
    )

    response = asyncio.run(verify_login(token, db=db, settings=settings))
    cookie = response.headers["set-cookie"]

    assert "serenity_session=" in cookie
    assert "Max-Age=15552000" in cookie
    assert "Domain=.usmonitor.app" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert session_cookie_domain(settings) == ".usmonitor.app"


def test_localhost_session_cookie_has_no_domain():
    settings = Settings(base_url="http://localhost:8000", secret_key="test-secret")

    assert session_cookie_domain(settings) is None


def test_me_renews_persistent_session_cookie():
    db = make_session()
    user = User(email="friend@example.com")
    db.add(user)
    db.commit()
    db.refresh(user)
    settings = Settings(base_url="https://usmonitor.app", secret_key="test-secret")
    response = Response()

    result = asyncio.run(me(response=response, user=user, db=db, settings=settings))
    cookie = response.headers["set-cookie"]

    assert result["email"] == "friend@example.com"
    assert "Max-Age=15552000" in cookie
    assert "Domain=.usmonitor.app" in cookie
