
from sqlalchemy.orm import Session

from models.restaurant import Restaurant
from utils.enums import UserRole
from utils.exceptions import ResourceNotFoundException

from repositories.dashboard_repository import (
    get_today_orders,
    get_pending_orders,
    get_completed_orders,
    get_cancelled_orders,
    get_today_revenue,
    get_monthly_revenue,
    get_most_ordered_food,
    get_average_rating,
    get_total_customers,
)


# ============================================================
# GET OWNER RESTAURANT
# ============================================================

def get_owner_restaurant(
    db: Session,
    current_user,
):

    if current_user.role != UserRole.RESTAURANT_OWNER:
        raise PermissionError(
            "Only restaurant owners can access the dashboard"
        )

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.owner_id == current_user.id
        )
        .first()
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    return restaurant


# ============================================================
# RESTAURANT DASHBOARD
# ============================================================

def get_restaurant_dashboard(
    db: Session,
    current_user,
):

    restaurant = get_owner_restaurant(
        db,
        current_user,
    )

    most_ordered_food = get_most_ordered_food(
        db,
        restaurant.id,
    )

    return {
        "today_orders": get_today_orders(
            db,
            restaurant.id,
        ),
        "pending_orders": get_pending_orders(
            db,
            restaurant.id,
        ),
        "completed_orders": get_completed_orders(
            db,
            restaurant.id,
        ),
        "cancelled_orders": get_cancelled_orders(
            db,
            restaurant.id,
        ),
        "today_revenue": get_today_revenue(
            db,
            restaurant.id,
        ),
        "monthly_revenue": get_monthly_revenue(
            db,
            restaurant.id,
        ),
        "most_ordered_food": most_ordered_food,
        "average_rating": get_average_rating(
            db,
            restaurant.id,
        ),
        "total_customers": get_total_customers(
            db,
            restaurant.id,
        ),
    }
