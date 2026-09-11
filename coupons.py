from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_roles
from models.user import User

from schemas.coupon import (
    CouponApplyRequest,
    CouponApplyResponse,
    CouponCreate,
    CouponResponse,
)

from services.coupon_service import (
    apply_coupon_service,
    create_coupon_service,
    get_all_coupons_service,
)

from utils.enums import UserRole

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


router = APIRouter(
    prefix="/coupons",
    tags=["Coupons"],
)


# ============================================================
# CREATE COUPON
# ============================================================

@router.post(
    "",
    response_model=CouponResponse,
    status_code=201,
)
def create_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
):

    try:

        return create_coupon_service(
            db=db,
            coupon_data=coupon_data,
        )

    except BusinessRuleException as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# GET ALL COUPONS
# ============================================================

@router.get(
    "",
    response_model=list[CouponResponse],
)
def get_coupons(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
):

    return get_all_coupons_service(db)


# ============================================================
# APPLY COUPON
# ============================================================

@router.post(
    "/apply",
    response_model=CouponApplyResponse,
)
def apply_coupon(
    coupon_data: CouponApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.CUSTOMER,
        )
    ),
):

    try:

        return apply_coupon_service(
            db=db,
            coupon_code=coupon_data.coupon_code,
            order_amount=coupon_data.order_amount,
        )

    except ResourceNotFoundException as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except BusinessRuleException as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )