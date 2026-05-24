from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import ManualPayment, MonitorList, Subscription, User, utcnow
from app.security import random_code


def get_or_create_pending_payment(
    db: Session, settings: Settings, user: User
) -> ManualPayment:
    payment = (
        db.query(ManualPayment)
        .filter(ManualPayment.user_id == user.id, ManualPayment.status == "pending")
        .order_by(ManualPayment.created_at.desc())
        .first()
    )
    if payment:
        return payment

    payment = ManualPayment(
        user_id=user.id,
        amount_usdt=settings.monthly_price_usdt,
        payment_code=random_code("SA-").upper(),
        receiving_address=(
            f"TRC20: {settings.usdt_trc20_address}\n"
            f"ERC20: {settings.usdt_erc20_address}"
        ).strip(),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def confirm_payment(
    db: Session, payment: ManualPayment, tx_hash: str = "", months: int = 1
) -> Subscription:
    payment.status = "confirmed"
    payment.tx_hash = tx_hash
    payment.confirmed_at = utcnow()

    monitor_list = db.query(MonitorList).filter(MonitorList.is_active.is_(True)).first()
    if not monitor_list:
        raise RuntimeError("No active monitor list exists")

    now = utcnow()
    current = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == payment.user_id,
            Subscription.monitor_list_id == monitor_list.id,
            Subscription.status == "active",
        )
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    start = max(now, current.expires_at) if current else now
    expires = start + timedelta(days=31 * max(1, months))

    subscription = Subscription(
        user_id=payment.user_id,
        monitor_list_id=monitor_list.id,
        starts_at=start,
        expires_at=expires,
        status="active",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription
