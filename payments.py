from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_roles
from models.user import User
from schemas.payment import (
    PaymentCreate,
    PaymentResponse,
)
from services.payment_service import (
    create_payment_service,
    get_order_payment_service,
    get_payment_service,
)
from utils.enums import UserRole
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


PAYMENT_ROLES = (
    UserRole.ADMIN,
    UserRole.CUSTOMER,
)


@router.post(
    "/{order_id}",
    response_model=PaymentResponse,
    status_code=201,
)
def create_payment(
    order_id: int,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*PAYMENT_ROLES)
    ),
):

    try:

        return create_payment_service(
            db=db,
            order_id=order_id,
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
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*PAYMENT_ROLES)
    ),
):

    try:

        return get_payment_service(
            db=db,
            payment_id=payment_id,
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




order_payment_router = APIRouter(
    prefix="/orders",
    tags=["Payments"],
)


@order_payment_router.get(
    "/{order_id}/payment",
    response_model=PaymentResponse,
)
def get_payment_for_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*PAYMENT_ROLES)
    ),
):

    try:

        return get_order_payment_service(
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