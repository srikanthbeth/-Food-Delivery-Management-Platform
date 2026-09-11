from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_roles
from models.user import User
from schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
)
from schemas.customer import (
    CustomerCreate,
    CustomerResponse,
)
from services.address_service import (
    create_address_service,
    get_customer_addresses_service,
    update_address_service,
)
from services.customer_service import (
    create_customer_service,
    get_customer_service,
)
from utils.enums import UserRole
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)

address_router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"],
)


MANAGE_ROLES = (
    UserRole.ADMIN,
    UserRole.CUSTOMER,
)


# ============================================================
# CUSTOMER
# ============================================================

@router.post(
    "",
    response_model=CustomerResponse,
    status_code=201,
)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return create_customer_service(
            db=db,
            customer_data=customer_data,
            current_user=current_user,
        )

    except BusinessRuleException as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return get_customer_service(
            db=db,
            customer_id=customer_id,
        )
    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# ADDRESSES UNDER CUSTOMER
# ============================================================

@router.post(
    "/{customer_id}/addresses",
    response_model=AddressResponse,
    status_code=201,
)
def create_address(
    customer_id: int,
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return create_address_service(
            db=db,
            customer_id=customer_id,
            address_data=address_data,
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
    "/{customer_id}/addresses",
    response_model=list[AddressResponse],
)
def get_customer_addresses(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return get_customer_addresses_service(
            db=db,
            customer_id=customer_id,
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
# ADDRESS UPDATE
# PUT /api/v1/addresses/{address_id}
# ============================================================

@address_router.put(
    "/{address_id}",
    response_model=AddressResponse,
)
def update_address(
    address_id: int,
    update_data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(*MANAGE_ROLES)
    ),
):
    try:
        return update_address_service(
            db=db,
            address_id=address_id,
            update_data=update_data,
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