from math import ceil

from sqlalchemy.orm import Session

from models.menu_item import MenuItem
from models.restaurant import Restaurant
from models.user import User

from repositories.menu_repository import (
    create_menu_item,
    delete_menu_item,
    get_all_menu_items,
    get_menu_item_by_id,
    search_menu_items,
    update_menu_item,
)

from utils.enums import UserRole

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


# ============================================================
# MENU ACCESS VALIDATION
# ============================================================

def validate_menu_access(
    current_user: User,
    restaurant: Restaurant,
):
    if current_user.role == UserRole.ADMIN:
        return

    if current_user.role == UserRole.RESTAURANT_OWNER:
        if restaurant.owner_id != current_user.id:
            raise BusinessRuleException(
                "Restaurant owner can only manage their own restaurant"
            )
        return

    if current_user.role == UserRole.RESTAURANT_STAFF:

        if current_user.restaurant_id is None:
            raise PermissionError(
                "Restaurant staff is not assigned to any restaurant"
            )

        if current_user.restaurant_id != restaurant.id:
            raise BusinessRuleException(
                "Restaurant staff can only manage their assigned restaurant"
            )

        return

    raise PermissionError(
        "Insufficient permissions"
    )


# ============================================================
# CREATE MENU ITEM
# ============================================================

def create_menu_item_service(
    db: Session,
    menu_data,
    current_user: User,
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == menu_data.restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    validate_menu_access(
        restaurant=restaurant,
        current_user=current_user,
    )

    menu_item = MenuItem(
        restaurant_id=menu_data.restaurant_id,
        category=menu_data.category,
        name=menu_data.name,
        description=menu_data.description,
        price=menu_data.price,
        preparation_time=menu_data.preparation_time,
        availability=menu_data.availability,
        vegetarian=menu_data.vegetarian,
        spicy_level=menu_data.spicy_level,
    )

    return create_menu_item(
        db,
        menu_item,
    )


# ============================================================
# GET ALL MENU ITEMS
# ============================================================

def get_menu_items_service(
    db: Session,
    restaurant_id: int | None = None,
):
    if restaurant_id is not None:

        restaurant = (
            db.query(Restaurant)
            .filter(
                Restaurant.id == restaurant_id
            )
            .first()
        )

        if not restaurant:
            raise ResourceNotFoundException(
                "Restaurant not found"
            )

    return get_all_menu_items(
        db,
        restaurant_id,
    )


# ============================================================
# FOOD SEARCH
# ============================================================

def search_menu_items_service(
    db: Session,
    restaurant_id: int | None = None,
    category: str | None = None,
    min_price=None,
    max_price=None,
    vegetarian: bool | None = None,
    spicy_level: int | None = None,
    availability: bool | None = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    # --------------------------------------------------------
    # VALIDATE RESTAURANT
    # --------------------------------------------------------

    if restaurant_id is not None:

        restaurant = (
            db.query(Restaurant)
            .filter(
                Restaurant.id == restaurant_id
            )
            .first()
        )

        if not restaurant:
            raise ResourceNotFoundException(
                "Restaurant not found"
            )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    items, total = search_menu_items(
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

    # --------------------------------------------------------
    # PAGE COUNT
    # --------------------------------------------------------

    pages = ceil(
        total / limit
    ) if total else 0

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
    }


# ============================================================
# GET MENU ITEM BY ID
# ============================================================

def get_menu_item_service(
    db: Session,
    menu_item_id: int,
):
    menu_item = get_menu_item_by_id(
        db,
        menu_item_id,
    )

    if not menu_item:
        raise ResourceNotFoundException(
            "Menu item not found"
        )

    return menu_item


# ============================================================
# UPDATE MENU ITEM
# ============================================================

def update_menu_item_service(
    db: Session,
    menu_item_id: int,
    update_data,
    current_user: User,
):
    menu_item = get_menu_item_by_id(
        db,
        menu_item_id,
    )

    if not menu_item:
        raise ResourceNotFoundException(
            "Menu item not found"
        )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == menu_item.restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    validate_menu_access(
        restaurant=restaurant,
        current_user=current_user,
    )

    data = update_data.model_dump(
        exclude_unset=True
    )

    return update_menu_item(
        db,
        menu_item,
        data,
    )


# ============================================================
# DELETE MENU ITEM
# ============================================================

def delete_menu_item_service(
    db: Session,
    menu_item_id: int,
    current_user: User,
):
    menu_item = get_menu_item_by_id(
        db,
        menu_item_id,
    )

    if not menu_item:
        raise ResourceNotFoundException(
            "Menu item not found"
        )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == menu_item.restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    validate_menu_access(
        restaurant=restaurant,
        current_user=current_user,
    )

    delete_menu_item(
        db,
        menu_item,
    )

    return {
        "success": True,
        "message": "Menu item deleted successfully",
    }