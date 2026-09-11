
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from schemas.notification import NotificationCreate
from services.notification_service import (
    create_notification_service,
)


def _add_notification(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int | None,
    notification_type: str,
    title: str,
    message: str,
):
    background_tasks.add_task(
        create_notification_service,
        db,
        NotificationCreate(
            customer_id=customer_id,
            order_id=order_id,
            notification_type=notification_type,
            title=title,
            message=message,
        ),
    )


def notify_order_placed(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "ORDER_PLACED",
        "Order Placed",
        "Your order has been placed successfully.",
    )


def notify_order_accepted(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "ORDER_ACCEPTED",
        "Order Accepted",
        "The restaurant has accepted your order.",
    )


def notify_food_ready(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "FOOD_READY",
        "Food Ready",
        "Your food is ready for pickup.",
    )


def notify_driver_assigned(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "DRIVER_ASSIGNED",
        "Driver Assigned",
        "A delivery partner has been assigned to your order.",
    )


def notify_out_for_delivery(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "OUT_FOR_DELIVERY",
        "Out for Delivery",
        "Your order is out for delivery.",
    )


def notify_order_delivered(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "ORDER_DELIVERED",
        "Order Delivered",
        "Your order has been delivered successfully.",
    )


def notify_payment_success(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "PAYMENT_SUCCESS",
        "Payment Successful",
        "Your payment was processed successfully.",
    )


def notify_refund_processed(
    background_tasks: BackgroundTasks,
    db: Session,
    customer_id: int,
    order_id: int,
):
    _add_notification(
        background_tasks,
        db,
        customer_id,
        order_id,
        "REFUND_PROCESSED",
        "Refund Processed",
        "Your refund has been processed successfully.",
    )
