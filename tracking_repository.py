from sqlalchemy.orm import Session

from models.order_tracking import OrderTracking


# ============================================================
# CREATE TRACKING
# ============================================================

def create_tracking(
    db: Session,
    tracking: OrderTracking,
) -> OrderTracking:

    db.add(tracking)

    db.commit()

    db.refresh(tracking)

    return tracking


# ============================================================
# GET TRACKING BY ID
# ============================================================

def get_tracking_by_id(
    db: Session,
    tracking_id: int,
) -> OrderTracking | None:

    return (
        db.query(OrderTracking)
        .filter(
            OrderTracking.id == tracking_id
        )
        .first()
    )


# ============================================================
# GET ORDER TRACKING
# ============================================================

def get_tracking_by_order(
    db: Session,
    order_id: int,
) -> list[OrderTracking]:

    return (
        db.query(OrderTracking)
        .filter(
            OrderTracking.order_id == order_id
        )
        .order_by(
            OrderTracking.timestamp.asc(),
            OrderTracking.id.asc(),
        )
        .all()
    )


# ============================================================
# GET LATEST TRACKING
# ============================================================

def get_latest_tracking(
    db: Session,
    order_id: int,
) -> OrderTracking | None:

    return (
        db.query(OrderTracking)
        .filter(
            OrderTracking.order_id == order_id
        )
        .order_by(
            OrderTracking.timestamp.desc(),
            OrderTracking.id.desc(),
        )
        .first()
    )