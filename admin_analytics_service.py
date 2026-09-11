from sqlalchemy.orm import Session

from utils.enums import UserRole
from repositories.admin_analytics_repository import (
    get_total_restaurants,
    get_total_customers,
    get_total_orders,
    get_total_revenue,
    get_total_refunds,
    get_active_delivery_partners,
    get_top_restaurants,
    get_top_food_items,
    get_most_popular_cuisine,
    get_daily_orders,
    get_monthly_revenue,
    get_cancellation_rate,
)


def get_admin_analytics(
    db: Session,
    current_user,
):
    if current_user.role != UserRole.ADMIN:
        raise PermissionError(
            "Only administrators can access analytics"
        )

    top_restaurants = get_top_restaurants(db)
    top_food_items = get_top_food_items(db)

    return {
        "total_restaurants": get_total_restaurants(db),
        "total_customers": get_total_customers(db),
        "total_orders": get_total_orders(db),
        "total_revenue": get_total_revenue(db),
        "total_refunds": get_total_refunds(db),
        "active_delivery_partners": get_active_delivery_partners(db),
        "top_restaurants": top_restaurants,
        "top_food_items": top_food_items,
        "most_popular_cuisine": get_most_popular_cuisine(db),
        "daily_orders": get_daily_orders(db),
        "monthly_revenue": get_monthly_revenue(db),
        "cancellation_rate": get_cancellation_rate(db),
    }