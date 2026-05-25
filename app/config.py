from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Serenity Alerts"
    base_url: str = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./serenity_alerts.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    admin_emails: tuple[str, ...] = tuple(_list_env("ADMIN_EMAILS"))

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    openai_summary_model: str = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-5.4-mini")
    openai_http_referer: str = os.getenv("OPENAI_HTTP_REFERER", "")
    openai_app_title: str = os.getenv("OPENAI_APP_TITLE", "US Monitor")
    x_bearer_token: str = os.getenv("X_BEARER_TOKEN", "")
    x_aleabitoreddit_user_id: str = os.getenv("X_ALEABITOREDDIT_USER_ID", "")

    massive_api_key: str = os.getenv("MASSIVE_API_KEY", "")
    massive_base_url: str = os.getenv(
        "MASSIVE_BASE_URL", "https://api.massive.com"
    ).rstrip("/")
    massive_cache_ttl_seconds: int = int(os.getenv("MASSIVE_CACHE_TTL_SECONDS", "60"))
    massive_request_concurrency: int = int(
        os.getenv("MASSIVE_REQUEST_CONCURRENCY", "12")
    )

    resend_api_key: str = os.getenv("RESEND_API_KEY", "")
    email_from: str = os.getenv(
        "EMAIL_FROM", "Serenity Alerts <alerts@example.com>"
    )

    vapid_public_key: str = os.getenv("VAPID_PUBLIC_KEY", "")
    vapid_private_key: str = os.getenv("VAPID_PRIVATE_KEY", "")
    vapid_contact: str = os.getenv("VAPID_CONTACT", "mailto:alerts@example.com")

    usdt_trc20_address: str = os.getenv("USDT_TRC20_ADDRESS", "")
    usdt_erc20_address: str = os.getenv("USDT_ERC20_ADDRESS", "")
    monthly_price_usdt: int = int(os.getenv("MONTHLY_PRICE_USDT", "99"))

    job_secret: str = os.getenv("JOB_SECRET", "")
    send_initial_backfill: bool = _bool_env("SEND_INITIAL_BACKFILL", False)

    magic_link_ttl_seconds: int = 15 * 60
    session_ttl_seconds: int = 30 * 24 * 60 * 60

    @property
    def secure_cookies(self) -> bool:
        return self.base_url.startswith("https://")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
