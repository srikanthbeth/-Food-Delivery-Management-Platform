import os
from datetime import datetime
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
from main import app

from models.user import User
from models.customer import Customer
from models.restaurant import Restaurant
from models.address import Address
from models.menu_item import MenuItem
from models.order import Order
from models.order_item import OrderItem
from models.review import Review

from utils.security import hash_password
from utils.enums import (
    UserRole,
    RestaurantStatus,
    OrderStatus,
    PaymentStatus,
)


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ============================================================
# HELPERS
# ============================================================

def unique_email():
    return f"dashboard_{uuid4().hex}@example.com"


def unique_phone():
    return f"9{uuid4().int % 1000000000:09d}"


def create_user(
    role=UserRole.CUSTOMER,
    email=None,
    full_name="Test User",
):
    db = SessionLocal()

    user = User(
        full_name=full_name,
        email=email or unique_email(),
        phone=unique_phone(),
        password_hash=hash_password("Test@123"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return user


def create_restaurant_owner():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Restaurant Owner",
    )

    db = SessionLocal()

    restaurant = Restaurant(
        restaurant_name=f"Dashboard Restaurant {uuid4().hex[:6]}",
        owner_id=owner.id,
        address="Test Restaurant Address",
        city="Hyderabad",
        phone=unique_phone(),
        cuisine_type="Indian",
        status=RestaurantStatus.OPEN,
        delivery_radius=10,
        opening_time=datetime.strptime("09:00", "%H:%M").time(),
        closing_time=datetime.strptime("23:00", "%H:%M").time(),
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    db.close()

    return owner, restaurant


def create_customer_user():
    user = create_user(
        role=UserRole.CUSTOMER,
        full_name="Dashboard Customer",
    )

    db = SessionLocal()

    customer = Customer(
        user_id=user.id,
        name="Dashboard Customer",
        email=user.email,
        phone=user.phone,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)
    db.close()

    return user, customer


def create_address(customer_id):
    db = SessionLocal()

    address = Address(
        customer_id=customer_id,
        address_line="123 Test Street",
        city="Hyderabad",
        pincode="500001",
        is_default=True,
    )

    db.add(address)
    db.commit()
    db.refresh(address)
    db.close()

    return address


def create_menu_item(
    restaurant_id,
    name="Chicken Biryani",
    price=250,
):
    db = SessionLocal()

    item = MenuItem(
        restaurant_id=restaurant_id,
        category="Main Course",
        name=name,
        description="Test food item",
        price=price,
        preparation_time=30,
        availability=True,
        vegetarian=False,
        spicy_level=2,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    db.close()

    return item


def create_order(
    customer_id,
    restaurant_id,
    address_id,
    order_status=OrderStatus.PENDING,
    total_amount=126,
):
    db = SessionLocal()

    order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        address_id=address_id,
        subtotal=100,
        delivery_fee=20,
        discount=0,
        tax=6,
        total_amount=total_amount,
        order_status=order_status,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)
    db.close()

    return order


def create_order_item(
    order_id,
    menu_item_id,
    quantity=1,
    unit_price=250,
):
    db = SessionLocal()

    item = OrderItem(
        order_id=order_id,
        menu_item_id=menu_item_id,
        quantity=quantity,
        unit_price=unit_price,
        item_total=quantity * unit_price,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    db.close()

    return item


def get_dashboard(user):
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "Test@123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/restaurants/dashboard",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    return response


# ============================================================
# OWNER ACCESS
# ============================================================

def test_restaurant_owner_can_access_dashboard():
    owner, restaurant = create_restaurant_owner()

    response = get_dashboard(owner)

    assert response.status_code == 200

    data = response.json()

    assert "today_orders" in data
    assert "pending_orders" in data
    assert "completed_orders" in data
    assert "cancelled_orders" in data
    assert "today_revenue" in data
    assert "monthly_revenue" in data
    assert "most_ordered_food" in data
    assert "average_rating" in data
    assert "total_customers" in data


# ============================================================
# EMPTY DASHBOARD
# ============================================================

def test_empty_dashboard():
    owner, restaurant = create_restaurant_owner()

    response = get_dashboard(owner)

    assert response.status_code == 200

    data = response.json()

    assert data["today_orders"] == 0
    assert data["pending_orders"] == 0
    assert data["completed_orders"] == 0
    assert data["cancelled_orders"] == 0
    assert data["today_revenue"] == 0
    assert data["monthly_revenue"] == 0
    assert data["most_ordered_food"] is None
    assert data["average_rating"] == 0
    assert data["total_customers"] == 0


# ============================================================
# TODAY ORDERS
# ============================================================

def test_today_orders():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.PENDING,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.ACCEPTED,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["today_orders"] == 2


# ============================================================
# PENDING ORDERS
# ============================================================

def test_pending_orders():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    pending_statuses = [
        OrderStatus.PENDING,
        OrderStatus.ACCEPTED,
        OrderStatus.PREPARING,
        OrderStatus.READY,
        OrderStatus.PICKED_UP,
        OrderStatus.OUT_FOR_DELIVERY,
    ]

    for order_status in pending_statuses:
        create_order(
            customer.id,
            restaurant.id,
            address.id,
            order_status,
        )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["pending_orders"] == 6


# ============================================================
# COMPLETED ORDERS
# ============================================================

def test_completed_orders():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["completed_orders"] == 2


# ============================================================
# CANCELLED ORDERS
# ============================================================

def test_cancelled_orders():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.CANCELLED,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.CANCELLED,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["cancelled_orders"] == 2


# ============================================================
# TODAY REVENUE
# ============================================================

def test_today_revenue():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
        total_amount=200,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
        total_amount=300,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.PENDING,
        total_amount=500,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["today_revenue"] == 500


# ============================================================
# MONTHLY REVENUE
# ============================================================

def test_monthly_revenue():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
        total_amount=400,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
        total_amount=600,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["monthly_revenue"] == 1000


# ============================================================
# MOST ORDERED FOOD
# ============================================================

def test_most_ordered_food():
    owner, restaurant = create_restaurant_owner()

    biryani = create_menu_item(
        restaurant.id,
        name="Chicken Biryani",
        price=250,
    )

    pizza = create_menu_item(
        restaurant.id,
        name="Chicken Pizza",
        price=300,
    )

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    order1 = create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    order2 = create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    create_order_item(
        order1.id,
        biryani.id,
        quantity=3,
        unit_price=250,
    )

    create_order_item(
        order2.id,
        biryani.id,
        quantity=2,
        unit_price=250,
    )

    create_order_item(
        order1.id,
        pizza.id,
        quantity=1,
        unit_price=300,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["most_ordered_food"] == "Chicken Biryani"


# ============================================================
# AVERAGE RATING
# ============================================================

def test_average_rating():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    order1 = create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    order2 = create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    db = SessionLocal()

    review1 = Review(
        customer_id=customer.id,
        order_id=order1.id,
        restaurant_id=restaurant.id,
        rating=5,
        review="Excellent",
    )

    review2 = Review(
        customer_id=customer.id,
        order_id=order2.id,
        restaurant_id=restaurant.id,
        rating=3,
        review="Good",
    )

    db.add_all([review1, review2])
    db.commit()
    db.close()

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["average_rating"] == 4.0


# ============================================================
# TOTAL CUSTOMERS
# ============================================================

def test_total_customers():
    owner, restaurant = create_restaurant_owner()

    customer_user1, customer1 = create_customer_user()
    address1 = create_address(customer1.id)

    customer_user2, customer2 = create_customer_user()
    address2 = create_address(customer2.id)

    create_order(
        customer1.id,
        restaurant.id,
        address1.id,
        OrderStatus.DELIVERED,
    )

    create_order(
        customer1.id,
        restaurant.id,
        address1.id,
        OrderStatus.DELIVERED,
    )

    create_order(
        customer2.id,
        restaurant.id,
        address2.id,
        OrderStatus.DELIVERED,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["total_customers"] == 2


# ============================================================
# AUTHENTICATION
# ============================================================

def test_dashboard_requires_authentication():
    response = client.get("/api/v1/restaurants/dashboard")

    assert response.status_code in [401, 403]


# ============================================================
# ROLE ACCESS
# ============================================================

def test_customer_cannot_access_dashboard():
    user, customer = create_customer_user()

    response = get_dashboard(user)

    assert response.status_code == 403


def test_admin_cannot_access_dashboard():
    admin = create_user(
        role=UserRole.ADMIN,
        full_name="Admin User",
    )

    response = get_dashboard(admin)

    assert response.status_code == 403


def test_delivery_partner_cannot_access_dashboard():
    delivery_partner = create_user(
        role=UserRole.DELIVERY_PARTNER,
        full_name="Delivery Partner",
    )

    response = get_dashboard(delivery_partner)

    assert response.status_code == 403


def test_restaurant_staff_cannot_access_dashboard():
    staff = create_user(
        role=UserRole.RESTAURANT_STAFF,
        full_name="Restaurant Staff",
    )

    response = get_dashboard(staff)

    assert response.status_code == 403


# ============================================================
# OWNER WITHOUT RESTAURANT
# ============================================================

def test_owner_without_restaurant_returns_404():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner Without Restaurant",
    )

    response = get_dashboard(owner)

    assert response.status_code == 404


# ============================================================
# DATA ISOLATION
# ============================================================

def test_owner_only_sees_own_restaurant_data():
    owner1, restaurant1 = create_restaurant_owner()
    owner2, restaurant2 = create_restaurant_owner()

    customer_user1, customer1 = create_customer_user()
    address1 = create_address(customer1.id)

    customer_user2, customer2 = create_customer_user()
    address2 = create_address(customer2.id)

    create_order(
        customer1.id,
        restaurant1.id,
        address1.id,
        OrderStatus.DELIVERED,
        total_amount=500,
    )

    create_order(
        customer2.id,
        restaurant2.id,
        address2.id,
        OrderStatus.DELIVERED,
        total_amount=1000,
    )

    response = get_dashboard(owner1)

    assert response.status_code == 200

    data = response.json()

    assert data["today_orders"] == 1
    assert data["completed_orders"] == 1
    assert data["today_revenue"] == 500
    assert data["monthly_revenue"] == 500
    assert data["total_customers"] == 1


# ============================================================
# UNIQUE CUSTOMER COUNT
# ============================================================

def test_total_customers_counts_distinct_customers():
    owner, restaurant = create_restaurant_owner()

    customer_user, customer = create_customer_user()
    address = create_address(customer.id)

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.PENDING,
    )

    response = get_dashboard(owner)

    assert response.status_code == 200
    assert response.json()["total_customers"] == 1