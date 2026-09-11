from sqlalchemy.orm import Session

from models.menu_item import MenuItem


def create_menu_item(
    db: Session,
    menu_item: MenuItem,
):
    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)

    return menu_item


def get_menu_item_by_id(
    db: Session,
    menu_item_id: int,
):
    return (
        db.query(MenuItem)
        .filter(MenuItem.id == menu_item_id)
        .first()
    )


def get_all_menu_items(
    db: Session,
    restaurant_id: int | None = None,
):
    query = db.query(MenuItem)

    if restaurant_id is not None:
        query = query.filter(
            MenuItem.restaurant_id == restaurant_id
        )

    return query.order_by(
        MenuItem.id.desc()
    ).all()


# ============================================================
# FOOD SEARCH
# ============================================================

def search_menu_items(
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
    query = db.query(MenuItem)

    # --------------------------------------------------------
    # FILTER BY RESTAURANT
    # --------------------------------------------------------

    if restaurant_id is not None:
        query = query.filter(
            MenuItem.restaurant_id == restaurant_id
        )

    # --------------------------------------------------------
    # FILTER BY CATEGORY
    # --------------------------------------------------------

    if category:
        query = query.filter(
            MenuItem.category.ilike(
                f"%{category}%"
            )
        )

    # --------------------------------------------------------
    # FILTER BY PRICE RANGE
    # --------------------------------------------------------

    if min_price is not None:
        query = query.filter(
            MenuItem.price >= min_price
        )

    if max_price is not None:
        query = query.filter(
            MenuItem.price <= max_price
        )

    # --------------------------------------------------------
    # VEGETARIAN FILTER
    # --------------------------------------------------------

    if vegetarian is not None:
        query = query.filter(
            MenuItem.vegetarian == vegetarian
        )

    # --------------------------------------------------------
    # SPICY LEVEL FILTER
    # --------------------------------------------------------

    if spicy_level is not None:
        query = query.filter(
            MenuItem.spicy_level == spicy_level
        )

    # --------------------------------------------------------
    # AVAILABILITY FILTER
    # --------------------------------------------------------

    if availability is not None:
        query = query.filter(
            MenuItem.availability == availability
        )

    # --------------------------------------------------------
    # SORTING
    # --------------------------------------------------------

    sort_columns = {
        "id": MenuItem.id,
        "name": MenuItem.name,
        "category": MenuItem.category,
        "price": MenuItem.price,
        "preparation_time": MenuItem.preparation_time,
        "spicy_level": MenuItem.spicy_level,
        "created_at": MenuItem.created_at,
    }

    sort_column = sort_columns.get(
        sort_by,
        MenuItem.created_at,
    )

    if sort_order == "asc":
        query = query.order_by(
            sort_column.asc()
        )
    else:
        query = query.order_by(
            sort_column.desc()
        )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total = query.count()

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    offset = (page - 1) * limit

    items = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return items, total


def update_menu_item(
    db: Session,
    menu_item: MenuItem,
    update_data: dict,
):
    for field, value in update_data.items():
        setattr(
            menu_item,
            field,
            value,
        )

    db.commit()
    db.refresh(menu_item)

    return menu_item


def delete_menu_item(
    db: Session,
    menu_item: MenuItem,
):
    db.delete(menu_item)
    db.commit()