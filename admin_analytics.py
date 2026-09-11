from pydantic import BaseModel, ConfigDict


class TopRestaurantAnalytics(BaseModel):
    restaurant_id: int
    restaurant_name: str
    order_count: int


class TopFoodItemAnalytics(BaseModel):
    menu_item_id: int
    food_name: str
    quantity_ordered: int


class AdminAnalyticsResponse(BaseModel):
    total_restaurants: int
    total_customers: int
    total_orders: int
    total_revenue: float
    total_refunds: float
    active_delivery_partners: int
    top_restaurants: list[TopRestaurantAnalytics]
    top_food_items: list[TopFoodItemAnalytics]
    most_popular_cuisine: str | None
    daily_orders: int
    monthly_revenue: float
    cancellation_rate: float

    model_config = ConfigDict(from_attributes=True)