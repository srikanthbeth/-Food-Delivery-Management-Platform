
import os
from uuid import uuid4

from decimal import Decimal

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
from models.delivery_partner import DeliveryPartner
from models.customer import Customer
from models.restaurant import Restaurant
from models.menu_item import MenuItem
from models.address import Address

from utils.enums import (
    UserRole,
    RestaurantStatus,
    DeliveryAvailabilityStatus,
    OrderStatus,
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


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_module():
    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )


def teardown_module():
    Base.metadata.drop_all(
        bind=test_engine
    )


# ============================================================
# HELPERS
# ============================================================

def create_user(
    role=UserRole.CUSTOMER,
    email=None,
    password="Password123",
):

    if email is None:
        email = (
            f"user_{uuid4().hex[:8]}"
            "@test.com"
        )

    db = TestingSessionLocal()

    user = User(
        full_name="Test User",
        email=email,
        phone="9876543210",
        password_hash=hash_password(
            password
        ),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    result = {
        "id": user.id,
        "email": user.email,
        "password": password,
        "role": role,
    }

    db.close()

    return result


def auth_headers(user):

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user["email"],
            "password": user["password"],
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_customer():

    user = create_user(
        role=UserRole.CUSTOMER
    )

    db = TestingSessionLocal()

    customer = Customer(
        user_id=user["id"],
        name="Test Customer",
        email=(
            f"customer_{uuid4().hex[:8]}"
            "@test.com"
        ),
        phone="9123456789",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    customer_id = customer.id

    db.close()

    return user, customer_id


def create_restaurant():

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    db = TestingSessionLocal()

    restaurant = Restaurant(
        restaurant_name=(
            f"Restaurant {uuid4().hex[:6]}"
        ),
        owner_id=owner["id"],
        address="123 Main Street",
        city="Hyderabad",
        phone="9000000000",
        cuisine_type="Indian",
        opening_time="09:00",
        closing_time="22:00",
        status=RestaurantStatus.OPEN,
        delivery_radius=10,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    restaurant_id = restaurant.id

    db.close()

    return owner, restaurant_id


def create_order_for_test():

    customer_user, customer_id = (
        create_customer()
    )

    owner, restaurant_id = (
        create_restaurant()
    )

    db = TestingSessionLocal()

    menu_item = MenuItem(
        restaurant_id=restaurant_id,
        category="Main Course",
        name="Test Biryani",
        description="Test food",
        price=Decimal("250.00"),
        preparation_time=20,
        availability=True,
        vegetarian=True,
        spicy_level=2,
    )

    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)

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

    menu_item_id = menu_item.id
    address_id = address.id

    db.close()

    # Add item to cart through API.
    response = client.post(
        "/api/v1/cart/items",
        params={
            "customer_id": customer_id,
        },
        json={
            "menu_item_id": menu_item_id,
            "quantity": 1,
        },
        headers=auth_headers(
            customer_user
        ),
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/orders",
        params={
            "customer_id": customer_id,
        },
        json={
            "address_id": address_id,
        },
        headers=auth_headers(
            customer_user
        ),
    )

    assert response.status_code == 201

    return (
        customer_user,
        response.json()["id"],
    )


def create_delivery_partner(
    admin,
    phone=None,
    vehicle_number=None,
):

    if phone is None:
        phone = (
            f"9{uuid4().int % 10**9:09d}"
        )

    if vehicle_number is None:
        vehicle_number = (
            f"TS{uuid4().hex[:8].upper()}"
        )

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Ravi Kumar",
            "phone": phone,
            "vehicle_type": "Bike",
            "vehicle_number": vehicle_number,
            "current_location": "Hyderabad",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 201

    return response.json()


# ============================================================
# CREATE DELIVERY PARTNER
# ============================================================

def test_admin_can_create_delivery_partner():

    admin = create_user(
        role=UserRole.ADMIN
    )

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Ravi Kumar",
            "phone": "9876500001",
            "vehicle_type": "Bike",
            "vehicle_number": "TS09AB1234",
            "current_location": "Hyderabad",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Ravi Kumar"
    assert body["phone"] == "9876500001"
    assert body["vehicle_type"] == "Bike"
    assert body["vehicle_number"] == "TS09AB1234"

    assert (
        body["availability_status"]
        == "Available"
    )


def test_customer_cannot_create_delivery_partner():

    customer = create_user(
        role=UserRole.CUSTOMER
    )

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Ravi Kumar",
            "phone": "9876500002",
            "vehicle_type": "Bike",
            "vehicle_number": "TS09AB1235",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 403


def test_restaurant_owner_cannot_create_delivery_partner():

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Ravi Kumar",
            "phone": "9876500003",
            "vehicle_type": "Bike",
            "vehicle_number": "TS09AB1236",
        },
        headers=auth_headers(owner),
    )

    assert response.status_code == 403


def test_delivery_partner_phone_must_be_unique():

    admin = create_user(
        role=UserRole.ADMIN
    )

    create_delivery_partner(
        admin,
        phone="9876500004",
    )

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Another Driver",
            "phone": "9876500004",
            "vehicle_type": "Car",
            "vehicle_number": "TS09AB9999",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Delivery partner phone already exists"
    )


def test_vehicle_number_must_be_unique():

    admin = create_user(
        role=UserRole.ADMIN
    )

    create_delivery_partner(
        admin,
        vehicle_number="TS09XY1111",
    )

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Another Driver",
            "phone": "9876500010",
            "vehicle_type": "Bike",
            "vehicle_number": "TS09XY1111",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Vehicle number already exists"
    )


def test_delivery_partner_phone_validation():

    admin = create_user(
        role=UserRole.ADMIN
    )

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Ravi Kumar",
            "phone": "abc123",
            "vehicle_type": "Bike",
            "vehicle_number": "TS09AA1000",
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 422


# ============================================================
# GET DELIVERY PARTNERS
# ============================================================

def test_admin_can_get_delivery_partners():

    admin = create_user(
        role=UserRole.ADMIN
    )

    create_delivery_partner(admin)

    response = client.get(
        "/api/v1/delivery-partners",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1


def test_restaurant_owner_can_get_delivery_partners():

    admin = create_user(
        role=UserRole.ADMIN
    )

    create_delivery_partner(admin)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    response = client.get(
        "/api/v1/delivery-partners",
        headers=auth_headers(owner),
    )

    assert response.status_code == 200


def test_restaurant_staff_can_get_delivery_partners():

    admin = create_user(
        role=UserRole.ADMIN
    )

    create_delivery_partner(admin)

    staff = create_user(
        role=UserRole.RESTAURANT_STAFF
    )

    response = client.get(
        "/api/v1/delivery-partners",
        headers=auth_headers(staff),
    )

    assert response.status_code == 200


def test_customer_cannot_get_delivery_partners():

    customer = create_user(
        role=UserRole.CUSTOMER
    )

    response = client.get(
        "/api/v1/delivery-partners",
        headers=auth_headers(customer),
    )

    assert response.status_code == 403


# ============================================================
# DRIVER STATUS
# ============================================================

def test_admin_can_set_driver_unavailable():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    response = client.put(
        f"/api/v1/delivery-partners/"
        f"{driver['id']}/status",
        json={
            "availability_status": "Unavailable"
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    assert (
        response.json()["availability_status"]
        == "Unavailable"
    )


def test_admin_can_set_driver_available():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    client.put(
        f"/api/v1/delivery-partners/"
        f"{driver['id']}/status",
        json={
            "availability_status": "Unavailable"
        },
        headers=auth_headers(admin),
    )

    response = client.put(
        f"/api/v1/delivery-partners/"
        f"{driver['id']}/status",
        json={
            "availability_status": "Available"
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    assert (
        response.json()["availability_status"]
        == "Available"
    )


def test_customer_cannot_update_driver_status():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    customer = create_user(
        role=UserRole.CUSTOMER
    )

    response = client.put(
        f"/api/v1/delivery-partners/"
        f"{driver['id']}/status",
        json={
            "availability_status": "Unavailable"
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 403


def test_driver_not_found_for_status_update():

    admin = create_user(
        role=UserRole.ADMIN
    )

    response = client.put(
        "/api/v1/delivery-partners/999999/status",
        json={
            "availability_status": "Unavailable"
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Delivery partner not found"
    )


# ============================================================
# ASSIGN DRIVER
# ============================================================

def test_admin_can_assign_available_driver():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    customer_user, order_id = (
        create_order_for_test()
    )

    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["order_id"] == order_id
    assert (
        body["delivery_partner_id"]
        == driver["id"]
    )

    assert (
        body["driver_status"]
        == "On Delivery"
    )


def test_unavailable_driver_cannot_be_assigned():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    client.put(
        f"/api/v1/delivery-partners/"
        f"{driver['id']}/status",
        json={
            "availability_status": "Unavailable"
        },
        headers=auth_headers(admin),
    )

    _, order_id = create_order_for_test()

    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Delivery partner is not available"
    )


def test_nonexistent_driver_cannot_be_assigned():

    admin = create_user(
        role=UserRole.ADMIN
    )

    _, order_id = create_order_for_test()

    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": 999999
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Delivery partner not found"
    )


def test_nonexistent_order_cannot_be_assigned():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    response = client.post(
        "/api/v1/orders/999999/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Order not found"
    )


def test_customer_cannot_assign_driver():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    customer, order_id = (
        create_order_for_test()
    )

    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 403


def test_restaurant_owner_can_assign_driver():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    owner, _ = create_restaurant()

    _, order_id = create_order_for_test()

    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(owner),
    )

    assert response.status_code == 200


def test_staff_can_assign_driver():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    staff = create_user(
        role=UserRole.RESTAURANT_STAFF
    )

    _, order_id = create_order_for_test()

    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(staff),
    )

    assert response.status_code == 200


# ============================================================
# DUPLICATE / CONFLICT ASSIGNMENT
# ============================================================

def test_driver_cannot_have_two_active_orders():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    _, first_order_id = (
        create_order_for_test()
    )

    first_response = client.post(
        f"/api/v1/orders/"
        f"{first_order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(admin),
    )

    assert first_response.status_code == 200

    _, second_order_id = (
        create_order_for_test()
    )

    response = client.post(
        f"/api/v1/orders/"
        f"{second_order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Delivery partner is not available"
    )


def test_order_cannot_have_two_drivers():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver1 = create_delivery_partner(
        admin
    )

    driver2 = create_delivery_partner(
        admin
    )

    _, order_id = create_order_for_test()

    first_response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver1["id"]
        },
        headers=auth_headers(admin),
    )

    assert first_response.status_code == 200

    # Make second driver available.
    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver2["id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Order already has a delivery partner"
    )


# ============================================================
# DELIVERED / CANCELLED ORDERS
# ============================================================

def test_delivered_order_cannot_get_driver():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    _, order_id = create_order_for_test()

    db = TestingSessionLocal()

    from models.order import Order

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
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 400


def test_cancelled_order_cannot_get_driver():

    admin = create_user(
        role=UserRole.ADMIN
    )

    driver = create_delivery_partner(
        admin
    )

    _, order_id = create_order_for_test()

    db = TestingSessionLocal()

    from models.order import Order

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id
        )
        .first()
    )

    order.order_status = (
        OrderStatus.CANCELLED
    )

    db.commit()
    db.close()

    response = client.post(
        f"/api/v1/orders/"
        f"{order_id}/assign-driver",
        params={
            "delivery_partner_id": driver["id"]
        },
        headers=auth_headers(admin),
    )

    assert response.status_code == 400


# ============================================================
# AUTHENTICATION
# ============================================================

def test_get_delivery_partners_requires_authentication():

    response = client.get(
        "/api/v1/delivery-partners"
    )

    assert response.status_code == 401


def test_create_delivery_partner_requires_authentication():

    response = client.post(
        "/api/v1/delivery-partners",
        json={
            "name": "Ravi Kumar",
            "phone": "9876500099",
            "vehicle_type": "Bike",
            "vehicle_number": "TS09ZZ9999",
        },
    )

    assert response.status_code == 401


def test_assign_driver_requires_authentication():

    response = client.post(
        "/api/v1/orders/1/assign-driver",
        params={
            "delivery_partner_id": 1
        },
    )

    assert response.status_code == 401

