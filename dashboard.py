
from pydantic import BaseModel


class RestaurantDashboardResponse(BaseModel):
    today_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    today_revenue: float
    monthly_revenue: float
    most_ordered_food: str | None
    average_rating: float
    total_customers: int
