from decimal import Decimal

from sqlalchemy.orm import Session

from models.order import Order
from models.order_item import OrderItem


def create_order(
    db: Session,
    order: Order,
) -> Order:

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def create_order_item(
    db: Session,
    order_item: OrderItem,
) -> OrderItem:

    db.add(order_item)
    db.commit()
    db.refresh(order_item)

    return order_item


def get_order_by_id(
    db: Session,
    order_id: int,
) -> Order | None:

    return (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )


def get_orders_by_customer(
    db: Session,
    customer_id: int,
) -> list[Order]:

    return (
        db.query(Order)
        .filter(
            Order.customer_id == customer_id
        )
        .order_by(
            Order.id.desc()
        )
        .all()
    )


def get_all_orders(
    db: Session,
) -> list[Order]:

    return (
        db.query(Order)
        .order_by(
            Order.id.desc()
        )
        .all()
    )


def search_orders(
    db: Session,
    customer_id: int | None = None,
    restaurant_id: int | None = None,
    delivery_partner_id: int | None = None,
    order_status=None,
    payment_status=None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    query = db.query(Order)

    # --------------------------------------------------------
    # FILTERS
    # --------------------------------------------------------

    if customer_id is not None:
        query = query.filter(
            Order.customer_id == customer_id
        )

    if restaurant_id is not None:
        query = query.filter(
            Order.restaurant_id == restaurant_id
        )

    if delivery_partner_id is not None:
        query = query.filter(
            Order.delivery_partner_id
            == delivery_partner_id
        )

    if order_status is not None:
        query = query.filter(
            Order.order_status == order_status
        )

    if payment_status is not None:
        query = query.filter(
            Order.payment_status == payment_status
        )

    if min_amount is not None:
        query = query.filter(
            Order.total_amount >= min_amount
        )

    if max_amount is not None:
        query = query.filter(
            Order.total_amount <= max_amount
        )

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    sort_columns = {
        "id": Order.id,
        "customer_id": Order.customer_id,
        "restaurant_id": Order.restaurant_id,
        "delivery_partner_id": Order.delivery_partner_id,
        "subtotal": Order.subtotal,
        "delivery_fee": Order.delivery_fee,
        "discount": Order.discount,
        "tax": Order.tax,
        "total_amount": Order.total_amount,
        "created_at": Order.created_at,
        "updated_at": Order.updated_at,
    }

    sort_column = sort_columns.get(
        sort_by,
        Order.id,
    )

    if sort_order == "asc":
        query = query.order_by(
            sort_column.asc()
        )
    else:
        query = query.order_by(
            sort_column.desc()
        )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total = query.count()

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    offset = (page - 1) * limit

    orders = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return orders, total


def update_order(
    db: Session,
    order: Order,
    **fields,
) -> Order:

    for field, value in fields.items():
        setattr(
            order,
            field,
            value,
        )

    db.commit()
    db.refresh(order)

    return order