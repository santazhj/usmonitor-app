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


async def send_login_code(
    settings: Settings, email: str, code: str, purpose: str = "login"
) -> dict:
    if not settings.resend_api_key:
        if settings.secure_cookies:
            raise RuntimeError("RESEND_API_KEY is required in production")
        return {"sent": False, "dev_code": code}

    subjects = {
        "register": "Your US Monitor registration code",
        "reset": "Your US Monitor password reset code",
        "login": "Your US Monitor verification code",
    }
    intro = {
        "register": "Your US Monitor registration code is:",
        "reset": "Your US Monitor password reset code is:",
        "login": "Your US Monitor verification code is:",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json={
                "from": settings.email_from,
                "to": [email],
                "subject": subjects.get(purpose, subjects["login"]),
                "html": (
                    f"<p>{intro.get(purpose, intro['login'])}</p>"
                    f"<p><strong style=\"font-size:24px;letter-spacing:4px;\">{code}</strong></p>"
                    "<p>This code expires in 15 minutes. If you did not request it, you can ignore this email.</p>"
                ),
            },
        )
        response.raise_for_status()
        return {"sent": True}
