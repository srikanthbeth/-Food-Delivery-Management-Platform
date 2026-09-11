from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.order import Order
from models.order_item import OrderItem
from models.menu_item import MenuItem
from models.review import Review
from utils.enums import OrderStatus


def get_today_orders(db: Session, restaurant_id: int) -> int:
    start = datetime.combine(
        datetime.today().date(),
        datetime.min.time(),
    )
    end = start + timedelta(days=1)

    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start,
            Order.created_at < end,
        )
        .count()
    )


def get_pending_orders(db: Session, restaurant_id: int) -> int:
    pending_statuses = [
        OrderStatus.PENDING,
        OrderStatus.ACCEPTED,
        OrderStatus.PREPARING,
        OrderStatus.READY,
        OrderStatus.PICKED_UP,
        OrderStatus.OUT_FOR_DELIVERY,
    ]

    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status.in_(pending_statuses),
        )
        .count()
    )


def get_completed_orders(db: Session, restaurant_id: int) -> int:
    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == OrderStatus.DELIVERED,
        )
        .count()
    )


def get_cancelled_orders(db: Session, restaurant_id: int) -> int:
    return (
        db.query(Order)
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.order_status == OrderStatus.CANCELLED,
        )
        .count()
    )


def get_today_revenue(db: Session, restaurant_id: int) -> float:
    start = datetime.combine(
        datetime.today().date(),
        datetime.min.time(),
    )
    end = start + timedelta(days=1)

    result = (
        db.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0,
            )
        )
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start,
            Order.created_at < end,
            Order.order_status == OrderStatus.DELIVERED,
        )
        .scalar()
    )

    return float(result or 0)


def get_monthly_revenue(db: Session, restaurant_id: int) -> float:
    today = datetime.today()

    start = today.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if today.month == 12:
        end = start.replace(
            year=today.year + 1,
            month=1,
        )
    else:
        end = start.replace(
            month=today.month + 1,
        )

    result = (
        db.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0,
            )
        )
        .filter(
            Order.restaurant_id == restaurant_id,
            Order.created_at >= start,
            Order.created_at < end,
            Order.order_status == OrderStatus.DELIVERED,
        )
        .scalar()
    )

    return float(result or 0)


def get_most_ordered_food(
    db: Session,
    restaurant_id: int,
):
    result = (
        db.query(
            MenuItem.name,
            func.sum(OrderItem.quantity).label(
                "order_count"
            ),
        )
        .join(
            OrderItem,
            OrderItem.menu_item_id == MenuItem.id,
        )
        .join(
            Order,
            Order.id == OrderItem.order_id,
        )
        .filter(
            Order.restaurant_id == restaurant_id,
        )
        .group_by(
            MenuItem.id,
            MenuItem.name,
        )
        .order_by(
            func.sum(OrderItem.quantity).desc()
        )
        .first()
    )

    if not result:
        return None

    return result[0]


def get_average_rating(
    db: Session,
    restaurant_id: int,
) -> float:
    result = (
        db.query(func.avg(Review.rating))
        .filter(
            Review.restaurant_id == restaurant_id,
        )
        .scalar()
    )

    return round(float(result or 0), 2)


def get_total_customers(
    db: Session,
    restaurant_id: int,
) -> int:
    result = (
        db.query(
            func.count(
                func.distinct(Order.customer_id)
            )
        )
        .filter(
            Order.restaurant_id == restaurant_id,
        )
        .scalar()
    )

    return int(result or 0)