
import os
from datetime import date, timedelta, time
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from main import app

from models.user import User
from models.restaurant import Restaurant
from models.menu_item import MenuItem
from models.customer import Customer
from models.address import Address
from models.cart import Cart
from models.cart_item import CartItem
from models.coupon import Coupon

from utils.enums import (
    UserRole,
    RestaurantStatus,
)

from utils.security import hash_password


# ============================================================
# TEST DATABASE
# ============================================================

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


# ============================================================
# TEST CLIENT
# ============================================================

client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    Base.metadata.drop_all(bind=test_engine)


# ============================================================
# HELPERS
# ============================================================

def create_user(
    role=UserRole.CUSTOMER,
    email=None,
    full_name="Test User",
    phone="9876543210",
    password="Password123",
):
    if email is None:
        email = f"user_{uuid4().hex[:8]}@test.com"

    db = TestingSessionLocal()

    user = User(
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    db.close()

    return {
        "id": user_id,
        "email": email,
        "password": password,
        "role": role,
    }


def login_user(user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(user):
    token = login_user(user)

    return {
        "Authorization": f"Bearer {token}"
    }


def create_customer(user=None):
    if user is None:
        user = create_user(
            role=UserRole.CUSTOMER
        )

    db = TestingSessionLocal()

    customer = Customer(
        user_id=user["id"],
        name="Test Customer",
        email=f"customer_{uuid4().hex[:8]}@test.com",
        phone="9876543210",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    customer_id = customer.id

    db.close()

    return customer_id


def create_restaurant(
    owner,
    status=RestaurantStatus.OPEN,
):
    db = TestingSessionLocal()

    restaurant = Restaurant(
        restaurant_name=f"Restaurant {uuid4().hex[:6]}",
        owner_id=owner["id"],
        address="123 Main Street",
        city="Hyderabad",
        phone="9876543210",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(22, 0),
        status=status,
        delivery_radius=10,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    restaurant_id = restaurant.id

    db.close()

    return restaurant_id


def create_menu_item(
    restaurant_id,
    name=None,
    price=Decimal("250.00"),
    availability=True,
):
    db = TestingSessionLocal()

    menu_item = MenuItem(
        restaurant_id=restaurant_id,
        category="Main Course",
        name=name or f"Food {uuid4().hex[:6]}",
        description="Test food item",
        price=price,
        preparation_time=20,
        availability=availability,
        vegetarian=True,
        spicy_level=2,
    )

    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)

    menu_item_id = menu_item.id

    db.close()

    return menu_item_id


def create_address(customer_id):
    db = TestingSessionLocal()

    address = Address(
        customer_id=customer_id,
        address_line="123 Test Street",
        city="Hyderabad",
        pincode="500001",
        latitude=17.385044,
        longitude=78.486671,
        address_type="Home",
        is_default=True,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    address_id = address.id

    db.close()

    return address_id


def add_item_to_cart(
    customer_id,
    menu_item_id,
    quantity=1,
):
    response = client.post(
        "/api/v1/cart/items",
        params={
            "customer_id": customer_id,
        },
        json={
            "menu_item_id": menu_item_id,
            "quantity": quantity,
        },
        headers=auth_headers_for_customer(
            customer_id
        ),
    )

    assert response.status_code == 201

    return response.json()


def auth_headers_for_customer(customer_id):
    db = TestingSessionLocal()

    customer = (
        db.query(Customer)
        .filter(
            Customer.id == customer_id
        )
        .first()
    )

    user = (
        db.query(User)
        .filter(
            User.id == customer.user_id
        )
        .first()
    )

    user_data = {
        "id": user.id,
        "email": user.email,
        "password": "Password123",
    }

    db.close()

    return auth_headers(user_data)


def create_coupon(
    admin,
    code=None,
    discount_type="Percentage",
    discount_value=10,
    minimum_order_value=Decimal("0.00"),
    maximum_discount=None,
    start_date=None,
    expiry_date=None,
    usage_limit=None,
    status=True,
):
    db = TestingSessionLocal()

    if start_date is None:
        start_date = date.today()

    if expiry_date is None:
        expiry_date = date.today() + timedelta(days=10)

    coupon = Coupon(
        coupon_code=(
            code
            or f"TEST{uuid4().hex[:6]}"
        ).upper(),
        discount_type=discount_type,
        discount_value=Decimal(
            str(discount_value)
        ),
        minimum_order_value=minimum_order_value,
        maximum_discount=maximum_discount,
        start_date=start_date,
        expiry_date=expiry_date,
        usage_limit=usage_limit,
        status=status,
        usage_count=0,
    )

    db.add(coupon)
    db.commit()
    db.refresh(coupon)

    coupon_code = coupon.coupon_code

    db.close()

    return coupon_code


def setup_order():
    customer_user = create_user(
        role=UserRole.CUSTOMER
    )

    customer_id = create_customer(
        customer_user
    )

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner
    )

    menu_item_id = create_menu_item(
        restaurant_id
    )

    address_id = create_address(
        customer_id
    )

    add_item_to_cart(
        customer_id,
        menu_item_id,
        quantity=2,
    )

    return {
        "customer_user": customer_user,
        "customer_id": customer_id,
        "owner": owner,
        "restaurant_id": restaurant_id,
        "menu_item_id": menu_item_id,
        "address_id": address_id,
    }


# ============================================================
# CREATE ORDER
# ============================================================

def test_create_order_success():

    data = setup_order()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["customer_id"] == data["customer_id"]
    assert body["restaurant_id"] == data["restaurant_id"]
    assert body["address_id"] == data["address_id"]

    assert body["subtotal"] == "500.00"
    assert body["delivery_fee"] == "40.00"
    assert body["tax"] == "25.00"
    assert body["discount"] == "0.00"
    assert body["total_amount"] == "565.00"

    assert body["order_status"] == "Pending"
    assert body["payment_status"] == "Pending"

    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 2


def test_order_requires_authentication():

    data = setup_order()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
    )

    assert response.status_code == 401


def test_customer_cannot_create_order_for_other_customer():

    data = setup_order()

    other_user = create_user(
        role=UserRole.CUSTOMER
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            other_user
        ),
    )

    assert response.status_code == 400

    assert (
        "own orders"
        in response.json()["detail"]
    )


def test_admin_can_create_order_for_customer():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 201


def test_cart_must_not_be_empty():

    customer_user = create_user(
        role=UserRole.CUSTOMER
    )

    customer_id = create_customer(
        customer_user
    )

    address_id = create_address(
        customer_id
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": customer_id
        },
        json={
            "address_id": address_id
        },
        headers=auth_headers(
            customer_user
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Cart is empty"
    )


def test_invalid_customer_rejected():

    user = create_user(
        role=UserRole.CUSTOMER
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": 999999
        },
        json={
            "address_id": 1
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Customer not found"
    )


def test_invalid_address_rejected():

    data = setup_order()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": 999999
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Address does not belong to customer"
    )


# ============================================================
# RESTAURANT VALIDATION
# ============================================================

def test_closed_restaurant_cannot_accept_order():

    data = setup_order()

    db = TestingSessionLocal()

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id
            == data["restaurant_id"]
        )
        .first()
    )

    restaurant.status = RestaurantStatus.CLOSED

    db.commit()
    db.close()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Restaurant is not accepting orders"
    )


def test_temporarily_unavailable_restaurant_cannot_accept_order():

    data = setup_order()

    db = TestingSessionLocal()

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id
            == data["restaurant_id"]
        )
        .first()
    )

    restaurant.status = (
        RestaurantStatus.TEMPORARILY_UNAVAILABLE
    )

    db.commit()
    db.close()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400


# ============================================================
# MENU ITEM VALIDATION
# ============================================================

def test_unavailable_menu_item_cannot_be_ordered():

    data = setup_order()

    db = TestingSessionLocal()

    menu_item = (
        db.query(MenuItem)
        .filter(
            MenuItem.id
            == data["menu_item_id"]
        )
        .first()
    )

    menu_item.availability = False

    db.commit()
    db.close()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert "unavailable" in (
        response.json()["detail"]
    )


# ============================================================
# PRICE / TOTAL CALCULATION
# ============================================================

def test_order_total_calculation():

    data = setup_order()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    subtotal = Decimal(
        body["subtotal"]
    )

    tax = Decimal(
        body["tax"]
    )

    delivery_fee = Decimal(
        body["delivery_fee"]
    )

    discount = Decimal(
        body["discount"]
    )

    total = Decimal(
        body["total_amount"]
    )

    assert total == (
        subtotal
        + tax
        + delivery_fee
        - discount
    )


# ============================================================
# COUPON
# ============================================================

def test_percentage_coupon_applied_to_order():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        discount_type="Percentage",
        discount_value=10,
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["subtotal"] == "500.00"
    assert body["discount"] == "50.00"
    assert body["tax"] == "25.00"
    assert body["delivery_fee"] == "40.00"
    assert body["total_amount"] == "515.00"


def test_fixed_coupon_applied_to_order():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        discount_type="Fixed",
        discount_value=100,
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["discount"] == "100.00"
    assert body["total_amount"] == "465.00"


def test_invalid_coupon_rejected():

    data = setup_order()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": "DOESNOTEXIST",
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Coupon not found"
    )


def test_expired_coupon_rejected():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        expiry_date=(
            date.today()
            - timedelta(days=1)
        ),
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Coupon has expired"
    )


def test_future_coupon_rejected():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        start_date=(
            date.today()
            + timedelta(days=2)
        ),
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Coupon is not active yet"
    )


def test_inactive_coupon_rejected():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        status=False,
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Coupon is inactive"
    )


def test_coupon_minimum_order_value_rejected():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        discount_value=10,
        minimum_order_value=Decimal(
            "1000.00"
        ),
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Minimum order value not satisfied"
    )


def test_coupon_maximum_discount_respected():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        discount_type="Percentage",
        discount_value=50,
        maximum_discount=Decimal(
            "50.00"
        ),
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["discount"] == "50.00"


def test_coupon_usage_limit_enforced():

    data = setup_order()

    admin = create_user(
        role=UserRole.ADMIN
    )

    coupon_code = create_coupon(
        admin,
        usage_limit=1,
    )

    first_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert first_response.status_code == 201

    second_data = setup_order()

    second_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": second_data["customer_id"]
        },
        json={
            "address_id": second_data["address_id"],
            "coupon_code": coupon_code,
        },
        headers=auth_headers(
            second_data["customer_user"]
        ),
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Coupon usage limit exceeded"
    )


# ============================================================
# CART CLEARING
# ============================================================

def test_cart_is_cleared_after_order():

    data = setup_order()

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 201

    db = TestingSessionLocal()

    cart = (
        db.query(Cart)
        .filter(
            Cart.customer_id
            == data["customer_id"]
        )
        .first()
    )

    assert cart is not None
    assert len(cart.items) == 0

    db.close()


# ============================================================
# GET ORDERS
# ============================================================

def test_customer_can_get_own_orders():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/orders",
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 200

    orders = response.json()

    assert len(orders) >= 1

    assert orders[0]["customer_id"] == (
        data["customer_id"]
    )


def test_admin_can_get_all_orders():

    data = setup_order()

    client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    admin = create_user(
        role=UserRole.ADMIN
    )

    response = client.get(
        "/api/v1/orders",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    orders = response.json()

    assert len(orders) >= 1


def test_customer_cannot_get_another_customer_order():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    other_user = create_user(
        role=UserRole.CUSTOMER
    )

    response = client.get(
        f"/api/v1/orders/{order_id}",
        headers=auth_headers(
            other_user
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "You can only access your own orders"
    )


def test_customer_can_get_own_order():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/orders/{order_id}",
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 200

    assert response.json()["id"] == order_id


def test_admin_can_get_order():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    order_id = create_response.json()["id"]

    admin = create_user(
        role=UserRole.ADMIN
    )

    response = client.get(
        f"/api/v1/orders/{order_id}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    assert response.json()["id"] == order_id


def test_order_not_found():

    user = create_user(
        role=UserRole.CUSTOMER
    )

    response = client.get(
        "/api/v1/orders/999999",
        headers=auth_headers(user),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Order not found"
    )


# ============================================================
# ORDER CANCELLATION
# ============================================================

def test_customer_can_cancel_pending_order():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["order_id"] == order_id
    assert body["order_status"] == "Cancelled"


def test_cancelled_order_cannot_be_cancelled_again():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    order_id = create_response.json()["id"]

    first_response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert second_response.status_code == 400

    assert second_response.json()["detail"] == (
        "Order is already cancelled"
    )


def test_delivered_order_cannot_be_cancelled():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]

    db = TestingSessionLocal()

    from models.order import Order
    from utils.enums import OrderStatus

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id
        )
        .first()
    )

    order.order_status = (
        OrderStatus.DELIVERED
    )

    db.commit()
    db.close()

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Delivered order cannot be cancelled"
    )


def test_ready_order_cannot_be_cancelled():

    data = setup_order()

    create_response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": data["customer_id"]
        },
        json={
            "address_id": data["address_id"]
        },
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    order_id = create_response.json()["id"]

    db = TestingSessionLocal()

    from models.order import Order
    from utils.enums import OrderStatus

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id
        )
        .first()
    )

    order.order_status = (
        OrderStatus.READY
    )

    db.commit()
    db.close()

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_headers(
            data["customer_user"]
        ),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Order cannot be cancelled at this stage"
    )


# ============================================================
# ROLE RESTRICTIONS
# ============================================================

def test_delivery_partner_cannot_get_orders():

    user = create_user(
        role=UserRole.DELIVERY_PARTNER
    )

    response = client.get(
        "/api/v1/orders",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


def test_restaurant_owner_cannot_get_orders():

    user = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    response = client.get(
        "/api/v1/orders",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


def test_restaurant_staff_cannot_get_orders():

    user = create_user(
        role=UserRole.RESTAURANT_STAFF
    )

    response = client.get(
        "/api/v1/orders",
        headers=auth_headers(user),
    )

    assert response.status_code == 403


def test_delivery_partner_cannot_create_order():

    user = create_user(
        role=UserRole.DELIVERY_PARTNER
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": 1
        },
        json={
            "address_id": 1
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 403


def test_restaurant_owner_cannot_create_order():

    user = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": 1
        },
        json={
            "address_id": 1
        },
        headers=auth_headers(user),
    )

    assert response.status_code == 403


# ============================================================
# AUTHENTICATION
# ============================================================

def test_get_orders_requires_authentication():

    response = client.get(
        "/api/v1/orders"
    )

    assert response.status_code == 401


def test_get_order_requires_authentication():

    response = client.get(
        "/api/v1/orders/1"
    )

    assert response.status_code == 401


def test_cancel_order_requires_authentication():

    response = client.post(
        "/api/v1/orders/1/cancel"
    )

    assert response.status_code == 401

