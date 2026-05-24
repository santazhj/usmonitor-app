from app.config import Settings
from app.models import PushSubscription
from app.services.push import send_push


def test_send_push_skips_without_vapid_keys():
    settings = Settings(vapid_private_key="", vapid_public_key="")
    subscription = PushSubscription(
        user_id="u1",
        endpoint="https://push.example.test/1",
        p256dh="key",
        auth="auth",
    )

    ok, message = send_push(settings, subscription, {"title": "Test"})

    assert ok
    assert "VAPID" in message
