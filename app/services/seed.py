from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import MonitorList, MonitoredSource


def seed_defaults(db: Session, settings: Settings) -> None:
    monitor_list = (
        db.query(MonitorList).filter(MonitorList.slug == "serenity-alert").one_or_none()
    )
    if not monitor_list:
        monitor_list = MonitorList(
            slug="serenity-alert",
            name="Serenity Alert",
            description=(
                "Curated AI supply-chain and market intelligence from selected X sources."
            ),
        )
        db.add(monitor_list)
        db.flush()

    source = (
        db.query(MonitoredSource)
        .filter(
            MonitoredSource.monitor_list_id == monitor_list.id,
            MonitoredSource.handle == "aleabitoreddit",
        )
        .one_or_none()
    )
    if not source:
        db.add(
            MonitoredSource(
                monitor_list_id=monitor_list.id,
                handle="aleabitoreddit",
                external_id=settings.x_aleabitoreddit_user_id,
                poll_interval_minutes=15,
            )
        )
    elif settings.x_aleabitoreddit_user_id and not source.external_id:
        source.external_id = settings.x_aleabitoreddit_user_id

    db.commit()
