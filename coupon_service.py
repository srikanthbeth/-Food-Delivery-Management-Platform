from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from models.coupon import Coupon

from repositories.coupon_repository import (
    create_coupon,
    get_all_coupons,
    get_coupon_by_code,
    get_coupon_by_id,
    increment_coupon_usage,
)

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


def create_coupon_service(
    db: Session,
    coupon_data,
) -> Coupon:

    existing_coupon = get_coupon_by_code(
        db,
        coupon_data.coupon_code,
    )

    if existing_coupon:
        raise BusinessRuleException(
            "Coupon code already exists"
        )

    coupon = Coupon(
        coupon_code=coupon_data.coupon_code,
        discount_type=coupon_data.discount_type,
        discount_value=coupon_data.discount_value,
        minimum_order_value=coupon_data.minimum_order_value,
        maximum_discount=coupon_data.maximum_discount,
        start_date=coupon_data.start_date,
        expiry_date=coupon_data.expiry_date,
        usage_limit=coupon_data.usage_limit,
        status=coupon_data.status,
    )

    return create_coupon(
        db,
        coupon,
    )


def get_all_coupons_service(
    db: Session,
):

    return get_all_coupons(db)


def get_coupon_service(
    db: Session,
    coupon_id: int,
):

    coupon = get_coupon_by_id(
        db,
        coupon_id,
    )

    if not coupon:
        raise ResourceNotFoundException(
            "Coupon not found"
        )

    return coupon


def apply_coupon_service(
    db: Session,
    coupon_code: str,
    order_amount: Decimal,
):

    coupon = get_coupon_by_code(
        db,
        coupon_code,
    )

    if not coupon:
        raise ResourceNotFoundException(
            "Coupon not found"
        )

    if not coupon.status:
        raise BusinessRuleException(
            "Coupon is inactive"
        )

    today = date.today()

    if today < coupon.start_date:
        raise BusinessRuleException(
            "Coupon is not active yet"
        )

    if today > coupon.expiry_date:
        raise BusinessRuleException(
            "Coupon has expired"
        )

    if (
        coupon.usage_limit is not None
        and coupon.usage_count >= coupon.usage_limit
    ):
        raise BusinessRuleException(
            "Coupon usage limit exceeded"
        )

    if order_amount < coupon.minimum_order_value:
        raise BusinessRuleException(
            "Minimum order value not satisfied"
        )

    if coupon.discount_type == "Percentage":

        discount_amount = (
            order_amount
            * coupon.discount_value
            / Decimal("100")
        )

        if coupon.maximum_discount is not None:
            discount_amount = min(
                discount_amount,
                coupon.maximum_discount,
            )

    else:
        discount_amount = coupon.discount_value

        if discount_amount > order_amount:
            discount_amount = order_amount

    discount_amount = discount_amount.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    final_amount = (
        order_amount - discount_amount
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    increment_coupon_usage(
        db,
        coupon,
    )

    return {
        "coupon_code": coupon.coupon_code,
        "order_amount": order_amount,
        "discount_amount": discount_amount,
        "final_amount": final_amount,
        "message": "Coupon applied successfully",
    }