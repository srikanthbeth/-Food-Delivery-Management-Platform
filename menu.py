from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_roles
from models.user import User
from schemas.menu_item import (
    MenuItemCreate,
    MenuItemResponse,
    MenuItemSearchResult,
    MenuItemUpdate,
)
from services.menu_service import (
    create_menu_item_service,
    delete_menu_item_service,
    get_menu_item_service,
    get_menu_items_service,
    search_menu_items_service,
    update_menu_item_service,
)
from utils.enums import UserRole
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


router = APIRouter(
    prefix="/menu",
    tags=["Menu"],
)


# ============================================================
# CREATE MENU ITEM
# ============================================================

@router.post(
    "/items",
    response_model=MenuItemResponse,
    status_code=201,
)
def create_menu_item(
    menu_data: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.RESTAURANT_OWNER,
            UserRole.RESTAURANT_STAFF,
        )
    ),
):
    try:
        return create_menu_item_service(
            db=db,
            menu_data=menu_data,
            current_user=current_user,
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

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )


# ============================================================
# GET ALL MENU ITEMS
# ============================================================

@router.get(
    "/items",
    response_model=list[MenuItemResponse],
)
def get_menu_items(
    restaurant_id: int | None = Query(
        default=None,
        gt=0,
    ),
    db: Session = Depends(get_db),
):
    try:
        return get_menu_items_service(
            db=db,
            restaurant_id=restaurant_id,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# FOOD SEARCH / FILTER / PAGINATION
# ============================================================

@router.get(
    "/items/search",
    response_model=MenuItemSearchResult,
)
def search_food_items(
    restaurant_id: int | None = Query(
        default=None,
        gt=0,
    ),
    category: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    min_price: Decimal | None = Query(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    ),
    max_price: Decimal | None = Query(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
    ),
    vegetarian: bool | None = None,
    spicy_level: int | None = Query(
        default=None,
        ge=0,
        le=5,
    ),
    availability: bool | None = None,
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
        "name",
        "category",
        "price",
        "preparation_time",
        "spicy_level",
        "created_at",
    ] = "created_at",
    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc",
    db: Session = Depends(get_db),
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=400,
            detail="Minimum price cannot be greater than maximum price",
        )

    try:
        return search_menu_items_service(
            db=db,
            restaurant_id=restaurant_id,
            category=category,
            min_price=min_price,
            max_price=max_price,
            vegetarian=vegetarian,
            spicy_level=spicy_level,
            availability=availability,
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


# ============================================================
# GET MENU ITEM BY ID
# ============================================================

@router.get(
    "/items/{menu_item_id}",
    response_model=MenuItemResponse,
)
def get_menu_item(
    menu_item_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_menu_item_service(
            db=db,
            menu_item_id=menu_item_id,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# UPDATE MENU ITEM
# ============================================================

@router.put(
    "/items/{menu_item_id}",
    response_model=MenuItemResponse,
)
def update_menu_item(
    menu_item_id: int,
    update_data: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.RESTAURANT_OWNER,
            UserRole.RESTAURANT_STAFF,
        )
    ),
):
    try:
        return update_menu_item_service(
            db=db,
            menu_item_id=menu_item_id,
            update_data=update_data,
            current_user=current_user,
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

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )


# ============================================================
# DELETE MENU ITEM
# ============================================================

@router.delete(
    "/items/{menu_item_id}",
)
def delete_menu_item(
    menu_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.RESTAURANT_OWNER,
            UserRole.RESTAURANT_STAFF,
        )
    ),
):
    try:
        return delete_menu_item_service(
            db=db,
            menu_item_id=menu_item_id,
            current_user=current_user,
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

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )