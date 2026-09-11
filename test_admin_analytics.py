import os

from datetime import datetime
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient

from database import (
    Base,
    SessionLocal,
    engine,
)

from main import app

from models.user import User
from models.customer import Customer
from models.restaurant import Restaurant
from models.address import Address
from models.menu_item import MenuItem
from models.order import Order
from models.order_item import OrderItem

from utils.security import hash_password

from utils.enums import (
    UserRole,
    RestaurantStatus,
    OrderStatus,
    PaymentStatus,
)


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email():
    return f"analytics_{uuid4().hex}@example.com"


def unique_phone():
    return f"9{uuid4().int % 1000000000:09d}"


def create_user(
    role=UserRole.CUSTOMER,
    full_name="Test User",
):
    db = SessionLocal()

    user = User(
        full_name=full_name,
        email=unique_email(),
        phone=unique_phone(),
        password_hash=hash_password(
            "Test@123"
        ),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    db.close()

    return user


def create_admin():
    return create_user(
        role=UserRole.ADMIN,
        full_name="Admin User",
    )


def create_customer():
    user = create_user(
        role=UserRole.CUSTOMER,
        full_name="Customer User",
    )

    db = SessionLocal()

    customer = Customer(
        user_id=user.id,
        name="Customer User",
        email=user.email,
        phone=user.phone,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    db.close()

    return user, customer


def create_restaurant(
    owner_id,
    name=None,
    cuisine="Indian",
):
    db = SessionLocal()

    restaurant = Restaurant(
        restaurant_name=(
            name
            or f"Restaurant {uuid4().hex[:6]}"
        ),
        owner_id=owner_id,
        address="Test Address",
        city="Hyderabad",
        phone=unique_phone(),
        cuisine_type=cuisine,
        status=RestaurantStatus.OPEN,
        delivery_radius=10,
        opening_time=datetime.strptime(
            "09:00",
            "%H:%M",
        ).time(),
        closing_time=datetime.strptime(
            "23:00",
            "%H:%M",
        ).time(),
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    db.close()

    return restaurant


def create_address(customer_id):
    db = SessionLocal()

    address = Address(
        customer_id=customer_id,
        address_line="Test Address",
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
        description="Test Food",
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
    status=OrderStatus.DELIVERED,
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
        order_status=status,
        payment_status=PaymentStatus.PAID,
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
        item_total=(
            quantity * unit_price
        ),
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    db.close()

    return item


def get_admin_dashboard():
    admin = create_admin()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": admin.email,
            "password": "Test@123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    return client.get(
        "/api/v1/admin/analytics",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )


def test_admin_can_access_analytics():
    response = get_admin_dashboard()

    assert response.status_code == 200

    data = response.json()

    assert "total_restaurants" in data
    assert "total_customers" in data
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "total_refunds" in data
    assert "active_delivery_partners" in data
    assert "top_restaurants" in data
    assert "top_food_items" in data
    assert "most_popular_cuisine" in data
    assert "daily_orders" in data
    assert "monthly_revenue" in data
    assert "cancellation_rate" in data


def test_total_restaurants():
    admin = create_admin()

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    create_restaurant(owner.id)
    create_restaurant(owner.id)

    response = get_admin_dashboard()

    assert response.status_code == 200

    assert (
        response.json()["total_restaurants"]
        >= 2
    )


def test_total_customers():
    create_customer()
    create_customer()

    response = get_admin_dashboard()

    assert response.status_code == 200

    assert (
        response.json()["total_customers"]
        >= 2
    )


def test_total_orders():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
    )

    response = get_admin_dashboard()

    assert response.status_code == 200

    assert (
        response.json()["total_orders"]
        >= 1
    )


def test_total_revenue():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
        500,
    )

    response = get_admin_dashboard()

    assert response.status_code == 200

    assert (
        response.json()["total_revenue"]
        >= 500
    )


def test_top_restaurants():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id,
        name="Top Restaurant",
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
    )

    for _ in range(3):
        create_order(
            customer.id,
            restaurant.id,
            address.id,
        )

    response = get_admin_dashboard()

    assert response.status_code == 200

    top = response.json()[
        "top_restaurants"
    ]

    assert len(top) >= 1

    assert any(
        item["restaurant_name"]
        == "Top Restaurant"
        for item in top
    )


def test_top_food_items():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id
    )

    food = create_menu_item(
        restaurant.id,
        "Biryani",
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
    )

    order = create_order(
        customer.id,
        restaurant.id,
        address.id,
    )

    create_order_item(
        order.id,
        food.id,
        quantity=5,
    )

    response = get_admin_dashboard()

    assert response.status_code == 200

    foods = response.json()[
        "top_food_items"
    ]

    assert len(foods) >= 1

    assert any(
        item["food_name"]
        == "Biryani"
        for item in foods
    )


def test_most_popular_cuisine():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id,
        cuisine="Indian",
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
    )

    response = get_admin_dashboard()

    assert response.status_code == 200

    assert (
        response.json()[
            "most_popular_cuisine"
        ]
        == "Indian"
    )


def test_daily_orders():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
    )

    response = get_admin_dashboard()

    assert response.status_code == 200

    assert (
        response.json()["daily_orders"]
        >= 1
    )


def test_monthly_revenue():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
    )

    create_order(
        customer.id,
        restaurant.id,
        address.id,
        OrderStatus.DELIVERED,
        750,
    )

    response = get_admin_dashboard()

    assert response.status_code == 200

    assert (
        response.json()["monthly_revenue"]
        >= 750
    )


def test_cancellation_rate():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    restaurant = create_restaurant(
        owner.id
    )

    _, customer = create_customer()

    address = create_address(
        customer.id
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
        OrderStatus.CANCELLED,
    )

    response = get_admin_dashboard()

    assert response.status_code == 200

    rate = response.json()[
        "cancellation_rate"
    ]

    assert rate >= 0
    assert rate <= 100


def test_customer_cannot_access_analytics():
    customer_user, _ = create_customer()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": customer_user.email,
            "password": "Test@123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/admin/analytics",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 403


def test_restaurant_owner_cannot_access_analytics():
    owner = create_user(
        role=UserRole.RESTAURANT_OWNER,
        full_name="Owner",
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": owner.email,
            "password": "Test@123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/api/v1/admin/analytics",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 403


def test_analytics_requires_authentication():
    response = client.get(
        "/api/v1/admin/analytics"
    )

    assert response.status_code in [
        401,
        403,
    ]