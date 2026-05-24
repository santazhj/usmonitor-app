from __future__ import annotations

import argparse
from datetime import timedelta

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models import InviteCode, utcnow
from app.security import random_code
from app.services.seed import seed_defaults


def init_database() -> None:
    init_db()
    with SessionLocal() as db:
        seed_defaults(db, get_settings())
    print("Database initialized")


def create_invite(label: str, max_uses: int) -> None:
    init_db()
    code = random_code("INV-").upper()
    with SessionLocal() as db:
        db.add(
            InviteCode(
                code=code,
                label=label,
                max_uses=max_uses,
                expires_at=utcnow() + timedelta(days=30),
            )
        )
        db.commit()
    print(code)


def generate_vapid() -> None:
    try:
        import base64

        from cryptography.hazmat.primitives import serialization
        from py_vapid import Vapid

        vapid = Vapid()
        vapid.generate_keys()
        private_raw = vapid.private_key.private_numbers().private_value.to_bytes(
            32, "big"
        )
        public_raw = vapid.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        private_key = base64.urlsafe_b64encode(private_raw).decode().rstrip("=")
        public_key = base64.urlsafe_b64encode(public_raw).decode().rstrip("=")
        print("VAPID_PUBLIC_KEY=" + public_key)
        print("VAPID_PRIVATE_KEY=" + private_key)
    except Exception as exc:
        raise SystemExit(f"Unable to generate VAPID keys: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    invite = sub.add_parser("create-invite")
    invite.add_argument("label")
    invite.add_argument("--max-uses", type=int, default=1)
    sub.add_parser("generate-vapid")
    args = parser.parse_args()

    if args.command == "init-db":
        init_database()
    elif args.command == "create-invite":
        create_invite(args.label, args.max_uses)
    elif args.command == "generate-vapid":
        generate_vapid()


if __name__ == "__main__":
    main()
