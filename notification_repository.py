
from sqlalchemy.orm import Session

from models.notification import Notification


def create_notification(
    db: Session,
    notification: Notification,
) -> Notification:
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_notification_by_id(
    db: Session,
    notification_id: int,
) -> Notification | None:
    return (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )


def get_customer_notifications(
    db: Session,
    customer_id: int,
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.customer_id == customer_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


def get_unread_notifications(
    db: Session,
    customer_id: int,
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(
            Notification.customer_id == customer_id,
            Notification.is_read.is_(False),
        )
        .order_by(Notification.created_at.desc())
        .all()
    )


def mark_notification_as_read(
    db: Session,
    notification: Notification,
) -> Notification:
    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification

