from __future__ import annotations

import re
from datetime import datetime

import httpx

from app.config import Settings

URL_RE = re.compile(r"https?://\S+")


class XClient:
    def __init__(self, settings: Settings):
        if not settings.x_bearer_token:
            raise RuntimeError("X_BEARER_TOKEN is not configured")
        self._headers = {"Authorization": f"Bearer {settings.x_bearer_token}"}

    async def get_user_id(self, handle: str) -> str:
        url = f"https://api.x.com/2/users/by/username/{handle}"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            return response.json()["data"]["id"]

    async def get_recent_posts(
        self, user_id: str, since_id: str | None = None, max_results: int = 10
    ) -> list[dict]:
        params: dict[str, str | int] = {
            "exclude": "retweets,replies",
            "max_results": max(5, min(max_results, 100)),
            "tweet.fields": "created_at,conversation_id,referenced_tweets,entities",
        }
        if since_id:
            params["since_id"] = since_id

        url = f"https://api.x.com/2/users/{user_id}/tweets"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url, headers=self._headers, params=params)
            response.raise_for_status()
            return response.json().get("data", [])


def parse_x_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def is_substantive_original(tweet: dict) -> bool:
    text = tweet.get("text", "").strip()
    if not text:
        return False

    referenced = tweet.get("referenced_tweets") or []
    quote_only = any(item.get("type") == "quoted" for item in referenced)
    stripped = URL_RE.sub("", text).strip()

    if quote_only and len(stripped) < 28:
        return False
    return len(stripped) >= 8
