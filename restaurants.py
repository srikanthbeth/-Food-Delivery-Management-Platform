from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user, require_roles
from models.user import User
from schemas.restaurant import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantSearchResult,
    RestaurantUpdate,
)
from services.restaurant_service import (
    create_restaurant_service,
    delete_restaurant_service,
    get_restaurant_service,
    get_restaurants_service,
    search_restaurants_service,
    update_restaurant_service,
)
from utils.enums import RestaurantStatus, UserRole
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"],
)


@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.RESTAURANT_OWNER,
        )
    ),
):
    try:
        return create_restaurant_service(
            db=db,
            restaurant_data=restaurant_data,
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


@router.get(
    "",
    response_model=list[RestaurantResponse],
)
def get_restaurants(
    db: Session = Depends(get_db),
):
    return get_restaurants_service(db)


@router.get(
    "/search",
    response_model=RestaurantSearchResult,
)
def search_restaurants(
    cuisine: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    city: Optional[str] = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    rating: Optional[float] = Query(
        default=None,
        ge=0,
        le=5,
    ),
    status_filter: Optional[RestaurantStatus] = Query(
        default=None,
        alias="status",
    ),
    delivery_time: Optional[float] = Query(
        default=None,
        gt=0,
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
        "restaurant_name",
        "city",
        "cuisine_type",
        "rating",
        "delivery_time",
        "created_at",
    ] = "created_at",
    sort_order: Literal[
        "asc",
        "desc",
    ] = "desc",
    db: Session = Depends(get_db),
):
    return search_restaurants_service(
        db=db,
        cuisine=cuisine,
        city=city,
        rating=rating,
        status=status_filter,
        delivery_time=delivery_time,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_restaurant_service(
            db,
            restaurant_id,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
)
def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.RESTAURANT_OWNER,
        )
    ),
):
    try:
        return update_restaurant_service(
            db=db,
            restaurant_id=restaurant_id,
            restaurant_data=restaurant_data,
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


@router.delete(
    "/{restaurant_id}",
)
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.RESTAURANT_OWNER,
        )
    ),
):
    try:
        return delete_restaurant_service(
            db=db,
            restaurant_id=restaurant_id,
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