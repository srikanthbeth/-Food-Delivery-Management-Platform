from math import ceil
from typing import Optional

from sqlalchemy.orm import Session

from models.restaurant import Restaurant
from models.user import User
from repositories.restaurant_repository import (
    create_restaurant,
    delete_restaurant,
    get_all_restaurants,
    get_restaurant_by_id,
    search_restaurants,
    update_restaurant,
)
from repositories.user_repository import get_user_by_id
from schemas.restaurant import RestaurantCreate, RestaurantUpdate
from utils.enums import UserRole
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


def create_restaurant_service(
    db: Session,
    restaurant_data: RestaurantCreate,
    current_user: User,
):
    # Admin can create for any valid owner.
    if current_user.role == UserRole.ADMIN:
        owner = get_user_by_id(
            db,
            restaurant_data.owner_id,
        )

        if not owner:
            raise ResourceNotFoundException(
                "Restaurant owner not found"
            )

        if owner.role != UserRole.RESTAURANT_OWNER:
            raise BusinessRuleException(
                "Restaurant owner must have Restaurant Owner role"
            )

    # Restaurant Owner can only create for themselves.
    elif current_user.role == UserRole.RESTAURANT_OWNER:
        if restaurant_data.owner_id != current_user.id:
            raise BusinessRuleException(
                "Restaurant owner can only create their own restaurant"
            )

    restaurant = Restaurant(
        restaurant_name=restaurant_data.restaurant_name,
        owner_id=restaurant_data.owner_id,
        address=restaurant_data.address,
        city=restaurant_data.city,
        phone=restaurant_data.phone,
        cuisine_type=restaurant_data.cuisine_type,
        opening_time=restaurant_data.opening_time,
        closing_time=restaurant_data.closing_time,
        status=restaurant_data.status,
        delivery_radius=restaurant_data.delivery_radius,
    )

    return create_restaurant(
        db,
        restaurant,
    )


def get_restaurants_service(
    db: Session,
):
    return get_all_restaurants(db)


def search_restaurants_service(
    db: Session,
    cuisine: Optional[str] = None,
    city: Optional[str] = None,
    rating: Optional[float] = None,
    status=None,
    delivery_time: Optional[float] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    rows, total = search_restaurants(
        db=db,
        cuisine=cuisine,
        city=city,
        rating=rating,
        status=status,
        delivery_time=delivery_time,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items = []

    for restaurant, restaurant_rating, restaurant_delivery_time in rows:
        items.append(
            {
                "id": restaurant.id,
                "restaurant_name": restaurant.restaurant_name,
                "owner_id": restaurant.owner_id,
                "address": restaurant.address,
                "city": restaurant.city,
                "phone": restaurant.phone,
                "cuisine_type": restaurant.cuisine_type,
                "opening_time": restaurant.opening_time,
                "closing_time": restaurant.closing_time,
                "status": restaurant.status,
                "delivery_radius": restaurant.delivery_radius,
                "rating": round(
                    float(restaurant_rating or 0),
                    2,
                ),
                "delivery_time": round(
                    float(
                        restaurant_delivery_time or 0
                    ),
                    2,
                ),
            }
        )

    pages = ceil(total / limit) if total else 0

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
    }


def get_restaurant_service(
    db: Session,
    restaurant_id: int,
):
    restaurant = get_restaurant_by_id(
        db,
        restaurant_id,
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    return restaurant


def update_restaurant_service(
    db: Session,
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    current_user: User,
):
    restaurant = get_restaurant_by_id(
        db,
        restaurant_id,
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    if (
        current_user.role != UserRole.ADMIN
        and restaurant.owner_id != current_user.id
    ):
        raise BusinessRuleException(
            "You can only update your own restaurant"
        )

    update_data = restaurant_data.model_dump(
        exclude_unset=True
    )

    opening_time = update_data.get(
        "opening_time",
        restaurant.opening_time,
    )

    closing_time = update_data.get(
        "closing_time",
        restaurant.closing_time,
    )

    if closing_time <= opening_time:
        raise BusinessRuleException(
            "Closing time must be after opening time"
        )

    for field, value in update_data.items():
        setattr(
            restaurant,
            field,
            value,
        )

    return update_restaurant(
        db,
        restaurant,
    )


def delete_restaurant_service(
    db: Session,
    restaurant_id: int,
    current_user: User,
):
    restaurant = get_restaurant_by_id(
        db,
        restaurant_id,
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    if (
        current_user.role != UserRole.ADMIN
        and restaurant.owner_id != current_user.id
    ):
        raise BusinessRuleException(
            "You can only delete your own restaurant"
        )

    delete_restaurant(
        db,
        restaurant,
    )

    return {
        "success": True,
        "message": "Restaurant deleted successfully",
    }