from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.restaurant import Restaurant
from models.customer import Customer
from models.order import Order
from models.order_item import OrderItem
from models.menu_item import MenuItem
from models.delivery_partner import DeliveryPartner
from models.refund import Refund

from utils.enums import (
    OrderStatus,
    DeliveryAvailabilityStatus,
    PaymentTransactionStatus,
)


def get_total_restaurants(db: Session) -> int:
    return db.query(Restaurant).count()


def get_total_customers(db: Session) -> int:
    return db.query(Customer).count()


def get_total_orders(db: Session) -> int:
    return db.query(Order).count()


def get_total_revenue(db: Session) -> float:
    result = (
        db.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0,
            )
        )
        .filter(
            Order.order_status == OrderStatus.DELIVERED,
        )
        .scalar()
    )

    return float(result or 0)


def get_total_refunds(db: Session) -> float:
    result = (
        db.query(
            func.coalesce(
                func.sum(Refund.amount),
                0,
            )
        )
        .filter(
            Refund.refund_status
            == PaymentTransactionStatus.SUCCESSFUL
        )
        .scalar()
    )

    return float(result or 0)


def get_active_delivery_partners(db: Session) -> int:
    return (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.availability_status
            == DeliveryAvailabilityStatus.AVAILABLE
        )
        .count()
    )


def get_top_restaurants(
    db: Session,
    limit: int = 5,
) -> list[dict]:
    results = (
        db.query(
            Restaurant.id,
            Restaurant.restaurant_name,
            func.count(Order.id).label("order_count"),
        )
        .join(
            Order,
            Order.restaurant_id == Restaurant.id,
        )
        .group_by(
            Restaurant.id,
            Restaurant.restaurant_name,
        )
        .order_by(
            func.count(Order.id).desc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "restaurant_id": row.id,
            "restaurant_name": row.restaurant_name,
            "order_count": row.order_count,
        }
        for row in results
    ]


def get_top_food_items(
    db: Session,
    limit: int = 5,
) -> list[dict]:
    results = (
        db.query(
            MenuItem.id,
            MenuItem.name,
            func.sum(OrderItem.quantity).label(
                "quantity_ordered"
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
            Order.order_status != OrderStatus.CANCELLED,
        )
        .group_by(
            MenuItem.id,
            MenuItem.name,
        )
        .order_by(
            func.sum(OrderItem.quantity).desc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "menu_item_id": row.id,
            "food_name": row.name,
            "quantity_ordered": int(
                row.quantity_ordered or 0
            ),
        }
        for row in results
    ]


def get_most_popular_cuisine(
    db: Session,
) -> str | None:
    result = (
        db.query(
            Restaurant.cuisine_type,
            func.count(Order.id).label("order_count"),
        )
        .join(
            Order,
            Order.restaurant_id == Restaurant.id,
        )
        .filter(
            Restaurant.cuisine_type.isnot(None),
            Order.order_status != OrderStatus.CANCELLED,
        )
        .group_by(
            Restaurant.cuisine_type,
        )
        .order_by(
            func.count(Order.id).desc(),
        )
        .first()
    )

    if not result:
        return None

    return result[0]


def get_daily_orders(
    db: Session,
) -> int:
    start = datetime.combine(
        datetime.today().date(),
        datetime.min.time(),
    )

    end = start + timedelta(days=1)

    return (
        db.query(Order)
        .filter(
            Order.created_at >= start,
            Order.created_at < end,
        )
        .count()
    )


def get_monthly_revenue(
    db: Session,
) -> float:
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
            Order.created_at >= start,
            Order.created_at < end,
            Order.order_status == OrderStatus.DELIVERED,
        )
        .scalar()
    )

    return float(result or 0)


def get_cancellation_rate(
    db: Session,
) -> float:
    total_orders = (
        db.query(func.count(Order.id))
        .scalar()
        or 0
    )

    if total_orders == 0:
        return 0.0

    cancelled_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.order_status == OrderStatus.CANCELLED,
        )
        .scalar()
        or 0
    )

    return round(
        (cancelled_orders / total_orders) * 100,
        2,
    )