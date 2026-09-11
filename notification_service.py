
from sqlalchemy.orm import Session

from models.customer import Customer
from models.notification import Notification
from models.order import Order
from repositories.notification_repository import (
    create_notification,
    get_customer_notifications,
    get_notification_by_id,
    get_unread_notifications,
    mark_notification_as_read,
)
from schemas.notification import NotificationCreate
from utils.enums import UserRole
from utils.exceptions import ResourceNotFoundException


def create_notification_service(
    db: Session,
    data: NotificationCreate,
) -> Notification:
    customer = (
        db.query(Customer)
        .filter(Customer.id == data.customer_id)
        .first()
    )

    if not customer:
        raise ResourceNotFoundException("Customer not found")

    if data.order_id is not None:
        order = (
            db.query(Order)
            .filter(Order.id == data.order_id)
            .first()
        )

        if not order:
            raise ResourceNotFoundException("Order not found")

        if order.customer_id != data.customer_id:
            raise ValueError(
                "Order does not belong to the customer"
            )

    notification = Notification(
        customer_id=data.customer_id,
        order_id=data.order_id,
        notification_type=data.notification_type,
        title=data.title,
        message=data.message,
        is_read=False,
    )

    return create_notification(db, notification)


def create_order_notification(
    db: Session,
    customer_id: int,
    order_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> Notification:
    data = NotificationCreate(
        customer_id=customer_id,
        order_id=order_id,
        notification_type=notification_type,
        title=title,
        message=message,
    )

    return create_notification_service(db, data)


def get_notifications_service(
    db: Session,
    current_user,
) -> list[Notification]:
    if current_user.role != UserRole.CUSTOMER:
        raise PermissionError(
            "Only customers can view notifications"
        )

    customer = (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .first()
    )

    if not customer:
        raise ResourceNotFoundException("Customer not found")

    return get_customer_notifications(
        db,
        customer.id,
    )


def get_unread_notifications_service(
    db: Session,
    current_user,
) -> list[Notification]:
    if current_user.role != UserRole.CUSTOMER:
        raise PermissionError(
            "Only customers can view notifications"
        )

    customer = (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .first()
    )

    if not customer:
        raise ResourceNotFoundException("Customer not found")

    return get_unread_notifications(
        db,
        customer.id,
    )


def mark_notification_read_service(
    db: Session,
    notification_id: int,
    current_user,
) -> Notification:
    if current_user.role != UserRole.CUSTOMER:
        raise PermissionError(
            "Only customers can update notifications"
        )

    notification = get_notification_by_id(
        db,
        notification_id,
    )

    if not notification:
        raise ResourceNotFoundException(
            "Notification not found"
        )

    customer = (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .first()
    )

    if not customer:
        raise ResourceNotFoundException("Customer not found")

    if notification.customer_id != customer.id:
        raise PermissionError(
            "You can only update your own notifications"
        )

    return mark_notification_as_read(
        db,
        notification,
    )

