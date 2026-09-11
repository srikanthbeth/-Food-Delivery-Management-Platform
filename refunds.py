from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_roles
from models.user import User
from schemas.order import OrderCancelResponse
from schemas.refund import (
    RefundCreate,
    RefundResponse,
)
from services.refund_service import (
    cancel_order_service,
    create_refund_service,
    get_refunds_service,
)
from utils.enums import UserRole
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


router = APIRouter(
    tags=[
        "Cancellation & Refund"
    ],
)


REFUND_ROLES = (
    UserRole.ADMIN,
    UserRole.CUSTOMER,
)


@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderCancelResponse,
)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*REFUND_ROLES)
    ),
):
    try:

        return cancel_order_service(
            db=db,
            order_id=order_id,
            current_user=current_user,
        )

    except ResourceNotFoundException as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    except BusinessRuleException as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "/payments/{payment_id}/refund",
    response_model=RefundResponse,
    status_code=201,
)
def create_refund(
    payment_id: int,
    data: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*REFUND_ROLES)
    ),
):
    try:

        return create_refund_service(
            db=db,
            payment_id=payment_id,
            data=data,
            current_user=current_user,
        )

    except ResourceNotFoundException as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    except BusinessRuleException as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/refunds",
    response_model=list[RefundResponse],
)
def get_refunds(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*REFUND_ROLES)
    ),
):
    try:

        return get_refunds_service(
            db=db,
            current_user=current_user,
        )

    except PermissionError as exc:

        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )