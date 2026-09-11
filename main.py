from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

from utils.exception_handlers import register_exception_handlers

from routes.auth import router as auth_router
from routes.restaurants import router as restaurant_router
from routes.menu import router as menu_router
from routes.customers import router as customer_router
from routes.customers import address_router
from routes.cart import router as cart_router
from routes.coupons import router as coupon_router
from routes.orders import router as order_router
from routes.delivery import router as delivery_router,order_delivery_router
from routes import tracking
from routes import payments
from routes import refunds
from routes import reviews
from routes.notifications import router as notification_router
from routes.dashboard import router as dashboard_router
from routes.admin_analytics import router as admin_analytics_router
from routes.audit_logs import router as audit_log_router

# ============================================================
# SWAGGER TAG ORDER
# ============================================================

openapi_tags = [
    {
        "name": "Authentication",
        "description": "Authentication and user management",
    },
    {
        "name": "Restaurants",
        "description": "Restaurant management",
    },
    {
        "name": "Menu",
        "description": "Menu and food item management",
    },
    {
        "name": "Customers",
        "description": "Customer and address management",
    },
    {
        "name": "Addresses",
        "description": "Address management",
    },
    {
        "name": "Cart",
        "description": "Shopping cart management",
    },
    {
        "name": "Coupons",
        "description": "Coupon and offer management",
    },
    {
        "name": "Orders",
        "description": "Order management",
    },
    {
        "name": "Delivery Partners",
        "description": "Delivery partner management and order assignment",
    },
    {
        "name": "Order Tracking",
        "description": "Order tracking management",
    },
    {
        "name": "Payments",
        "description": "Payment management",
    },
    {
        "name": "Cancellation & Refund",
        "description": "Order cancellation and refund management",
    },
    {
    "name": "Reviews & Ratings",
    "description": "Customer reviews and ratings",
    },

    {
        "name": "Notifications",
        "description": "Customer notifications",
    },
    {
        "name": "Restaurant Dashboard",
        "description": "Restaurant dashboard and performance metrics",
    },
    {
        "name": "Admin Analytics",
        "description": "Administrative analytics and platform statistics",
    },
]


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Restaurant & Food Delivery Management System",
    description=(
        "Complete Restaurant and Food Delivery "
        "Management Platform"
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

register_exception_handlers(app)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"]
        if settings.CORS_ORIGINS == "*"
        else settings.CORS_ORIGINS.split(",")
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LEVEL 1 - AUTHENTICATION
# ============================================================

app.include_router(
    auth_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 15 - RESTAURANT DASHBOARD
#
# IMPORTANT:
# This router must be registered BEFORE the restaurant
# router because /restaurants/{restaurant_id} can otherwise
# capture /restaurants/dashboard.
#
# Swagger display order is controlled separately by
# openapi_tags above.
# ============================================================

app.include_router(
    dashboard_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 16 - ADMIN ANALYTICS
#
# Registered early for routing purposes.
# Swagger display order remains Level 16 because of
# openapi_tags.
# ============================================================

app.include_router(
    admin_analytics_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 2 - RESTAURANTS
# ============================================================

app.include_router(
    restaurant_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 3 - MENU
# ============================================================

app.include_router(
    menu_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 4 - CUSTOMER & ADDRESS
# ============================================================

app.include_router(
    customer_router,
    prefix="/api/v1",
)

app.include_router(
    address_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 5 - CART
# ============================================================

app.include_router(
    cart_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 6 - COUPONS / OFFERS
# ============================================================

app.include_router(
    coupon_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 7 - ORDERS
# ============================================================

app.include_router(
    order_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 8 - DELIVERY
# ============================================================

app.include_router(
    delivery_router,
    prefix="/api/v1",
)

app.include_router(
    order_delivery_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 9 - ORDER TRACKING
# ============================================================

app.include_router(
    tracking.router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 10 - PAYMENTS
# ============================================================

app.include_router(
    payments.router,
    prefix="/api/v1",
)

app.include_router(
    payments.order_payment_router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 11 - CANCELLATION & REFUND
# ============================================================

app.include_router(
    refunds.router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 12 - REVIEWS
# ============================================================

app.include_router(
    reviews.router,
    prefix="/api/v1",
)


# ============================================================
# LEVEL 14 - NOTIFICATIONS
# ============================================================

app.include_router(
    notification_router,
    prefix="/api/v1",
)

app.include_router(
    audit_log_router,
    prefix="/api/v1",
)
# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "success": True,
        "message": (
            "Restaurant Food Delivery API "
            "is running"
        ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "success": True,
        "message": "API is healthy",
    }