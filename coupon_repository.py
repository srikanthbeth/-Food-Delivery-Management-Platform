from sqlalchemy.orm import Session

from models.coupon import Coupon


def create_coupon(
    db: Session,
    coupon: Coupon,
) -> Coupon:

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    return coupon


def get_coupon_by_id(
    db: Session,
    coupon_id: int,
) -> Coupon | None:

    return (
        db.query(Coupon)
        .filter(
            Coupon.id == coupon_id
        )
        .first()
    )


def get_coupon_by_code(
    db: Session,
    coupon_code: str,
) -> Coupon | None:

    return (
        db.query(Coupon)
        .filter(
            Coupon.coupon_code == coupon_code
        )
        .first()
    )


def get_all_coupons(
    db: Session,
) -> list[Coupon]:

    return (
        db.query(Coupon)
        .order_by(Coupon.id.desc())
        .all()
    )


def increment_coupon_usage(
    db: Session,
    coupon: Coupon,
) -> Coupon:

    coupon.usage_count += 1

    db.commit()
    db.refresh(coupon)

    return coupon