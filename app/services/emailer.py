from __future__ import annotations

import httpx

from app.config import Settings


async def send_magic_link(settings: Settings, email: str, link: str) -> dict:
    if not settings.resend_api_key:
        if settings.secure_cookies:
            raise RuntimeError("RESEND_API_KEY is required in production")
        return {"sent": False, "dev_magic_link": link}

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.email_from,
                "to": [email],
                "subject": "Your Serenity Alerts login link",
                "html": (
                    "<p>Open this link to sign in to Serenity Alerts:</p>"
                    f'<p><a href="{link}">{link}</a></p>'
                    "<p>This link expires in 15 minutes.</p>"
                ),
            },
        )
        response.raise_for_status()
        return {"sent": True}
