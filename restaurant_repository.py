from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.menu_item import MenuItem
from models.restaurant import Restaurant
from models.review import Review


def create_restaurant(db: Session, restaurant: Restaurant):
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def get_restaurant_by_id(db: Session, restaurant_id: int):
    return (
        db.query(Restaurant)
        .filter(Restaurant.id == restaurant_id)
        .first()
    )


def get_all_restaurants(db: Session):
    return (
        db.query(Restaurant)
        .order_by(Restaurant.id.desc())
        .all()
    )


def search_restaurants(
    db: Session,
    cuisine: Optional[str] = None,
    city: Optional[str] = None,
    rating: Optional[float] = None,
    status=None,
    delivery_time: Optional[float] = None,
    page: int = 1,
    limit: int = 10,
    sort_by: str = "id",
    sort_order: str = "desc",
):
    rating_subquery = (
        db.query(
            Review.restaurant_id.label("restaurant_id"),
            func.avg(Review.rating).label("rating"),
        )
        .group_by(Review.restaurant_id)
        .subquery()
    )

    preparation_subquery = (
        db.query(
            MenuItem.restaurant_id.label("restaurant_id"),
            func.avg(MenuItem.preparation_time).label("delivery_time"),
        )
        .group_by(MenuItem.restaurant_id)
        .subquery()
    )

    query = (
        db.query(
            Restaurant,
            func.coalesce(rating_subquery.c.rating, 0).label("rating"),
            func.coalesce(
                preparation_subquery.c.delivery_time, 0
            ).label("delivery_time"),
        )
        .outerjoin(
            rating_subquery,
            Restaurant.id == rating_subquery.c.restaurant_id,
        )
        .outerjoin(
            preparation_subquery,
            Restaurant.id == preparation_subquery.c.restaurant_id,
        )
    )

    if cuisine:
        query = query.filter(
            Restaurant.cuisine_type.ilike(f"%{cuisine}%")
        )

    if city:
        query = query.filter(
            Restaurant.city.ilike(f"%{city}%")
        )

    if status is not None:
        query = query.filter(Restaurant.status == status)

    if rating is not None:
        query = query.filter(
            func.coalesce(rating_subquery.c.rating, 0) >= rating
        )

    if delivery_time is not None:
        query = query.filter(
            func.coalesce(
                preparation_subquery.c.delivery_time, 0
            ) <= delivery_time
        )

    sort_columns = {
        "id": Restaurant.id,
        "name": Restaurant.restaurant_name,
        "city": Restaurant.city,
        "cuisine": Restaurant.cuisine_type,
        "rating": func.coalesce(rating_subquery.c.rating, 0),
        "delivery_time": func.coalesce(
            preparation_subquery.c.delivery_time, 0
        ),
        "created_at": Restaurant.created_at,
    }

    sort_column = sort_columns.get(sort_by, Restaurant.id)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()

    offset = (page - 1) * limit

    rows = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return rows, total


def update_restaurant(
    db: Session,
    restaurant: Restaurant,
):
    db.commit()
    db.refresh(restaurant)

    return restaurant


def delete_restaurant(
    db: Session,
    restaurant: Restaurant,
):
    db.delete(restaurant)
    db.commit()