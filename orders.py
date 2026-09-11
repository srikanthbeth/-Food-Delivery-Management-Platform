from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from decimal import Decimal
from typing import Literal
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_roles
from models.user import User

from schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderSearchResult,
)

from services.order_service import (
    create_order_service,
    get_order_service,
    get_orders_service,
    search_orders_service,
)

from utils.enums import UserRole

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)

from utils.enums import (
    UserRole,
    OrderStatus,
    PaymentStatus,
)


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


MANAGE_ROLES = (
    UserRole.ADMIN,
    UserRole.CUSTOMER,
)


# ============================================================
# CREATE ORDER
# ============================================================

@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
)
def create_order(
    order_data: OrderCreate,
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return create_order_service(
            db=db,
            customer_id=customer_id,
            order_data=order_data,
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


# ============================================================
# GET ORDERS
# ============================================================

@router.get(
    "",
    response_model=list[OrderResponse],
)
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return get_orders_service(
            db=db,
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



# ============================================================
# SEARCH ORDERS
# ============================================================

@router.get(
    "/search",
    response_model=OrderSearchResult,
)
def search_orders(
    customer_id: int | None = Query(
        default=None,
        gt=0,
    ),
    restaurant_id: int | None = Query(
        default=None,
        gt=0,
    ),
    delivery_partner_id: int | None = Query(
        default=None,
        gt=0,
    ),
    order_status: OrderStatus | None = Query(
        default=None,
    ),
    payment_status: PaymentStatus | None = Query(
        default=None,
    ),
    min_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    max_amount: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    sort_by: Literal[
        "id",
        "customer_id",
        "restaurant_id",
        "delivery_partner_id",
        "subtotal",
        "delivery_fee",
        "discount",
        "tax",
        "total_amount",
        "created_at",
        "updated_at",
    ] = "id",
    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return search_orders_service(
            db=db,
            current_user=current_user,
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            delivery_partner_id=delivery_partner_id,
            order_status=order_status,
            payment_status=payment_status,
            min_amount=min_amount,
            max_amount=max_amount,
            page=page,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
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


# ============================================================
# GET ORDER BY ID
# ============================================================

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return get_order_service(
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