from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, ManualPayment, MonitorList, User
from app.services.payments import confirm_payment


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_confirm_payment_creates_active_subscription():
    db = make_session()
    user = User(email="friend@example.com")
    monitor_list = MonitorList(slug="serenity-alert", name="Serenity Alert")
    db.add_all([user, monitor_list])
    db.commit()
    payment = ManualPayment(
        user_id=user.id,
        amount_usdt=99,
        payment_code="SA-TEST",
        status="pending",
    )
    db.add(payment)
    db.commit()

    subscription = confirm_payment(db, payment, tx_hash="0xabc", months=1)

    assert payment.status == "confirmed"
    assert payment.tx_hash == "0xabc"
    assert subscription.user_id == user.id
    assert subscription.monitor_list_id == monitor_list.id
    assert subscription.status == "active"
    assert subscription.expires_at > subscription.starts_at
