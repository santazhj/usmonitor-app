from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AlertSummary, Delivery, PushSubscription, utcnow


def notification_payload(summary: AlertSummary) -> dict:
    return {
        "title": summary.title,
        "body": summary.notification_text,
        "url": f"/?alert={summary.id}",
        "source_url": summary.source_url,
    }


def send_push(
    settings: Settings, subscription: PushSubscription, payload: dict
) -> tuple[bool, str]:
    if not settings.vapid_private_key or not settings.vapid_public_key:
        return True, "push skipped: VAPID keys are not configured"

    try:
        from pywebpush import WebPushException, webpush

        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_contact},
            ttl=60 * 60,
        )
        return True, ""
    except Exception as exc:
        message = str(exc)
        if "410" in message or "404" in message:
            return False, message
        return False, message


def deliver_summary_to_subscribers(
    db: Session, settings: Settings, summary: AlertSummary
) -> dict[str, int]:
    active_pushes = (
        db.query(PushSubscription)
        .join(PushSubscription.user)
        .filter(PushSubscription.is_active.is_(True))
        .all()
    )
    sent = 0
    failed = 0
    payload = notification_payload(summary)

    for push in active_pushes:
        user_has_subscription = any(
            sub.monitor_list_id == summary.monitor_list_id
            and sub.status == "active"
            and sub.expires_at > utcnow()
            for sub in push.user.subscriptions
        )
        if not user_has_subscription:
            continue

        ok, error = send_push(settings, push, payload)
        delivery = Delivery(
            summary_id=summary.id,
            push_subscription_id=push.id,
            user_id=push.user_id,
            status="sent" if ok else "failed",
            error=error,
            sent_at=utcnow() if ok else None,
        )
        db.add(delivery)
        if ok:
            push.last_success_at = utcnow()
            sent += 1
        else:
            failed += 1
            if "410" in error or "404" in error:
                push.is_active = False
                push.disabled_at = utcnow()

    db.commit()
    return {"sent": sent, "failed": failed}
