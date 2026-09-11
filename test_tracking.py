from datetime import datetime, time
from uuid import uuid4

from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
from main import app

from models.address import Address
from models.order import Order
from models.order_tracking import OrderTracking
from models.restaurant import Restaurant
from models.user import User
from models.customer import Customer

from utils.enums import (
    OrderStatus,
    PaymentStatus,
    TrackingStatus,
    UserRole,
)

from utils.security import hash_password


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

def unique_email(prefix="tracking"):
    """
    Create a valid unique email address.

    Spaces are replaced because role values such as
    'Restaurant Owner' would otherwise create invalid emails.
    """
    prefix = prefix.replace(" ", "_").lower()

    return (
        f"{prefix}_{uuid4().hex[:10]}"
        "@example.com"
    )


def create_user(
    role: UserRole = UserRole.CUSTOMER,
    email: str | None = None,
):
    db = SessionLocal()

    user = User(
        full_name=f"Tracking {role.value} User",
        email=email or unique_email(),
        phone=f"9{uuid4().int % 10**9:09d}",
        password_hash=hash_password("Test@12345"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    db.close()

    return user_id


def login_user(
    email: str,
    password: str = "Test@12345",
):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    token = (
        data.get("access_token")
        or data.get("data", {}).get("access_token")
    )

    assert token is not None

    return token


def create_user_and_login(
    role: UserRole,
):
    db = SessionLocal()

    email = unique_email(role.value)

    user = User(
        full_name=f"Tracking {role.value}",
        email=email,
        phone=f"8{uuid4().int % 10**9:09d}",
        password_hash=hash_password("Test@12345"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.flush()

    customer_id = user.id

    if role == UserRole.CUSTOMER:
        customer = Customer(
            user_id=user.id,
            name=f"Tracking Customer {uuid4().hex[:8]}",
            email=email,
            phone=user.phone,
        )

        db.add(customer)
        db.flush()

        customer_id = customer.id

    db.commit()
    db.refresh(user)

    user_id = user.id
    db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return customer_id, token

def create_restaurant(
    db,
    owner_id: int,
):
    restaurant = Restaurant(
        restaurant_name=(
            f"Tracking Restaurant "
            f"{uuid4().hex[:8]}"
        ),
        owner_id=owner_id,
        address="Tracking Test Address",
        city="Hyderabad",
        phone=f"7{uuid4().int % 10**9:09d}",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(23, 0),
        status="Open",
        delivery_radius=10,
    )

    db.add(restaurant)
    db.flush()

    return restaurant


def create_address(
    db,
    customer_id: int,
):
    address = Address(
        customer_id=customer_id,
        address_line="Tracking Test Address",
        city="Hyderabad",
        pincode="500001",
        latitude=17.3850,
        longitude=78.4867,
        address_type="Home",
        is_default=True,
    )

    db.add(address)
    db.flush()

    return address

def create_order(
    customer_id: int,
    status: OrderStatus = OrderStatus.PENDING,
    delivery_partner_id: int | None = None,
):
    """
    Create all required parent records before creating the order.

    The Order model requires valid:
        customer_id
        restaurant_id
        address_id
    """

    db = SessionLocal()

    # --------------------------------------------------------
    # Restaurant
    # --------------------------------------------------------

    restaurant = create_restaurant(
        db=db,
        owner_id=customer_id,
    )

    # --------------------------------------------------------
    # Customer Address
    # --------------------------------------------------------

    address = create_address(
        db=db,
        customer_id=customer_id,
    )

    # --------------------------------------------------------
    # Order
    # --------------------------------------------------------

    order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        delivery_partner_id=delivery_partner_id,
        subtotal=100,
        delivery_fee=40,
        discount=0,
        tax=5,
        total_amount=145,
        order_status=status,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    order_id = order.id

    db.close()

    return order_id


def create_tracking_record(
    order_id: int,
    status: TrackingStatus = TrackingStatus.PENDING,
    location: str = "Hyderabad",
    remarks: str = "Order received",
):
    db = SessionLocal()

    tracking = OrderTracking(
        order_id=order_id,
        status=status,
        location=location,
        remarks=remarks,
    )

    db.add(tracking)
    db.commit()
    db.refresh(tracking)

    tracking_id = tracking.id

    db.close()

    return tracking_id


# ============================================================
# AUTHENTICATION
# ============================================================

def test_get_tracking_requires_authentication():

    response = client.get(
        "/api/v1/orders/999999/tracking"
    )

    assert response.status_code in (401, 403)


def test_create_tracking_requires_authentication():

    response = client.post(
        "/api/v1/orders/999999/tracking",
        json={
            "status": "Pending",
            "location": "Hyderabad",
            "remarks": "Order received",
        },
    )

    assert response.status_code in (401, 403)


# ============================================================
# ORDER NOT FOUND
# ============================================================

def test_get_tracking_order_not_found():

    customer_id, token = create_user_and_login(
        UserRole.CUSTOMER
    )

    response = client.get(
        "/api/v1/orders/999999/tracking",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_create_tracking_order_not_found():

    _, token = create_user_and_login(
        UserRole.ADMIN
    )

    response = client.post(
        "/api/v1/orders/999999/tracking",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Pending",
            "location": "Hyderabad",
            "remarks": "Order received",
        },
    )

    assert response.status_code == 404


# ============================================================
# CUSTOMER TRACKING ACCESS
# ============================================================

def test_customer_can_view_own_order_tracking():

    customer_id, token = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.PENDING,
        location="Hyderabad",
        remarks="Order placed",
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["order_id"] == order_id
    assert data[0]["status"] == "Pending"
    assert data[0]["location"] == "Hyderabad"


def test_customer_cannot_view_other_customer_tracking():

    customer_1_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    customer_2_id, token_2 = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_1_id
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {token_2}"
        },
    )

    assert response.status_code == 403


# ============================================================
# CREATE TRACKING
# ============================================================

def test_admin_can_create_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "Accepted",
            "location": "Restaurant",
            "remarks": "Restaurant accepted the order",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order_id
    assert data["status"] == "Accepted"
    assert data["location"] == "Restaurant"
    assert data["remarks"] == "Restaurant accepted the order"
    assert data["id"] > 0


def test_restaurant_owner_can_create_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, owner_token = create_user_and_login(
        UserRole.RESTAURANT_OWNER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {owner_token}"
        },
        json={
            "status": "Preparing",
            "location": "Restaurant Kitchen",
            "remarks": "Food is being prepared",
        },
    )

    assert response.status_code == 201


def test_restaurant_staff_can_create_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, staff_token = create_user_and_login(
        UserRole.RESTAURANT_STAFF
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {staff_token}"
        },
        json={
            "status": "Ready",
            "location": "Restaurant",
            "remarks": "Food is ready",
        },
    )

    assert response.status_code == 201


# ============================================================
# CUSTOMER CANNOT CREATE TRACKING
# ============================================================

def test_customer_cannot_create_tracking():

    customer_id, token = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Accepted",
            "location": "Restaurant",
            "remarks": "Accepted",
        },
    )

    assert response.status_code == 403


# ============================================================
# DELIVERED ORDER
# ============================================================

def test_delivered_order_cannot_receive_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id,
        status=OrderStatus.DELIVERED,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "Delivered",
            "location": "Customer Address",
            "remarks": "Delivered",
        },
    )

    assert response.status_code == 400


# ============================================================
# CANCELLED ORDER
# ============================================================

def test_cancelled_order_cannot_receive_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id,
        status=OrderStatus.CANCELLED,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "Cancelled",
            "location": "Restaurant",
            "remarks": "Order cancelled",
        },
    )

    assert response.status_code == 400


# ============================================================
# TRACKING STATUS VALIDATION
# ============================================================

def test_invalid_tracking_status():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "Invalid Status",
            "location": "Hyderabad",
            "remarks": "Invalid",
        },
    )

    assert response.status_code == 422


# ============================================================
# OPTIONAL FIELDS
# ============================================================

def test_tracking_location_and_remarks_optional():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "Accepted"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order_id
    assert data["status"] == "Accepted"
    assert data["location"] is None
    assert data["remarks"] is None


# ============================================================
# EMPTY TEXT VALIDATION
# ============================================================

def test_tracking_empty_location_becomes_none():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "Accepted",
            "location": "   ",
            "remarks": "Accepted",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["location"] is None


# ============================================================
# TRACKING HISTORY
# ============================================================

def test_get_multiple_tracking_records():

    customer_id, token = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.PENDING,
        location="Restaurant",
        remarks="Order placed",
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.ACCEPTED,
        location="Restaurant",
        remarks="Order accepted",
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.PREPARING,
        location="Kitchen",
        remarks="Food preparation started",
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3

    assert data[0]["status"] == "Pending"
    assert data[1]["status"] == "Accepted"
    assert data[2]["status"] == "Preparing"


# ============================================================
# TRACKING STATUS FLOW
# ============================================================

def test_tracking_status_flow():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    statuses = [
        "Pending",
        "Accepted",
        "Preparing",
        "Ready",
        "Picked Up",
        "Out for Delivery",
    ]

    for status in statuses:

        response = client.post(
            f"/api/v1/orders/{order_id}/tracking",
            headers={
                "Authorization": f"Bearer {admin_token}"
            },
            json={
                "status": status,
                "location": "Hyderabad",
                "remarks": f"Status changed to {status}",
            },
        )

        assert response.status_code == 201

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == len(statuses)

    returned_statuses = [
        item["status"]
        for item in data
    ]

    assert returned_statuses == statuses


# ============================================================
# TRACKING TIMESTAMP
# ============================================================

def test_tracking_contains_timestamp():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "status": "Accepted",
            "location": "Hyderabad",
            "remarks": "Accepted",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["timestamp"] is not None


# ============================================================
# TRACKING ISOLATION
# ============================================================

def test_tracking_belongs_to_correct_order():

    customer_id, token = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_1 = create_order(
        customer_id=customer_id
    )

    order_2 = create_order(
        customer_id=customer_id
    )

    create_tracking_record(
        order_id=order_1,
        status=TrackingStatus.ACCEPTED,
    )

    response = client.get(
        f"/api/v1/orders/{order_2}/tracking",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data == []


# ============================================================
# ADMIN CAN VIEW TRACKING
# ============================================================

def test_admin_can_view_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.ACCEPTED,
        location="Restaurant",
        remarks="Accepted",
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["status"] == "Accepted"


# ============================================================
# RESTAURANT OWNER CAN VIEW TRACKING
# ============================================================

def test_restaurant_owner_can_view_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, owner_token = create_user_and_login(
        UserRole.RESTAURANT_OWNER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.PREPARING,
        location="Kitchen",
        remarks="Preparing food",
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {owner_token}"
        },
    )

    assert response.status_code == 200


# ============================================================
# RESTAURANT STAFF CAN VIEW TRACKING
# ============================================================

def test_restaurant_staff_can_view_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, staff_token = create_user_and_login(
        UserRole.RESTAURANT_STAFF
    )

    order_id = create_order(
        customer_id=customer_id
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.READY,
        location="Restaurant",
        remarks="Food ready",
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {staff_token}"
        },
    )

    assert response.status_code == 200


# ============================================================
# DELIVERY PARTNER CAN VIEW TRACKING
# ============================================================

def test_delivery_partner_can_view_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, driver_token = create_user_and_login(
        UserRole.DELIVERY_PARTNER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    create_tracking_record(
        order_id=order_id,
        status=TrackingStatus.OUT_FOR_DELIVERY,
        location="Hyderabad",
        remarks="Out for delivery",
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {driver_token}"
        },
    )

    assert response.status_code == 200


# ============================================================
# DELIVERY PARTNER CAN CREATE TRACKING
# ============================================================

def test_delivery_partner_can_create_tracking():

    customer_id, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, driver_token = create_user_and_login(
        UserRole.DELIVERY_PARTNER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/tracking",
        headers={
            "Authorization": f"Bearer {driver_token}"
        },
        json={
            "status": "Out for Delivery",
            "location": "Hyderabad",
            "remarks": "Driver started delivery",
        },
    )

    assert response.status_code == 201
