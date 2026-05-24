import time

from app.security import sign_payload, verify_payload


def test_signed_payload_roundtrip():
    token = sign_payload({"typ": "session", "uid": "u1"}, "secret", 30)

    payload = verify_payload(token, "secret")

    assert payload["typ"] == "session"
    assert payload["uid"] == "u1"


def test_signed_payload_rejects_bad_secret():
    token = sign_payload({"typ": "session", "uid": "u1"}, "secret", 30)

    assert verify_payload(token, "other") is None


def test_signed_payload_expires():
    token = sign_payload({"typ": "session", "uid": "u1"}, "secret", -1)

    assert verify_payload(token, "secret") is None
