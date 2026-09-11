
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

from models.customer import Customer
from models.notification import Notification
from models.order import Order
from models.user import User

from utils.security import hash_password
from utils.enums import (
    OrderStatus,
    PaymentStatus,
    UserRole,
)


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ============================================================
# HELPERS
# ============================================================

def unique_email(prefix="notification"):
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def unique_phone():
    return str(
        9000000000
        + int(uuid4().hex[:8], 16) % 999999999
    )


def create_user(
    role=UserRole.CUSTOMER,
    prefix="notification",
):
    db = SessionLocal()

    email = unique_email(prefix)
    phone = unique_phone()

    user = User(
        full_name="Notification Test User",
        email=email,
        phone=phone,
        password_hash=hash_password("Test@123"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    customer = None

    if role == UserRole.CUSTOMER:
        customer = Customer(
            user_id=user.id,
            name="Notification Customer",
            email=email,
            phone=phone,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

    user_id = user.id
    customer_id = customer.id if customer else None

    db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test@123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return user_id, customer_id, token


def create_order(customer_id):
    db = SessionLocal()

    from models.address import Address
    from models.restaurant import Restaurant

    # --------------------------------------------------------
    # Restaurant owner
    # --------------------------------------------------------

    owner = User(
        full_name="Notification Restaurant Owner",
        email=unique_email("owner"),
        phone=unique_phone(),
        password_hash=hash_password("Owner@123"),
        role=UserRole.RESTAURANT_OWNER,
        is_active=True,
    )

    db.add(owner)
    db.commit()
    db.refresh(owner)

    # --------------------------------------------------------
    # Restaurant
    # --------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name="Notification Restaurant",
        owner_id=owner.id,
        address="Test Restaurant Address",
        city="Hyderabad",
        phone=unique_phone(),
        cuisine_type="Indian",
        status="Open",
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

    # --------------------------------------------------------
    # Customer address
    # --------------------------------------------------------

    address = Address(
        customer_id=customer_id,
        address_line="Notification Test Address",
        city="Hyderabad",
        pincode="500001",
        is_default=True,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # --------------------------------------------------------
    # Order
    # --------------------------------------------------------

    order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=100,
        delivery_fee=20,
        discount=0,
        tax=6,
        total_amount=126,
        order_status=OrderStatus.PENDING,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    order_id = order.id

    db.close()

    return order_id


def create_notification(
    customer_id,
    order_id=None,
    notification_type="ORDER_PLACED",
    title="Order Placed",
    message="Your order has been placed successfully.",
):
    db = SessionLocal()

    notification = Notification(
        customer_id=customer_id,
        order_id=order_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    notification_id = notification.id

    db.close()

    return notification_id


# ============================================================
# CREATE NOTIFICATION
# ============================================================

def test_create_order_notification():
    _, customer_id, _ = create_user(
        prefix="create_order_notification"
    )

    order_id = create_order(customer_id)

    notification_id = create_notification(
        customer_id=customer_id,
        order_id=order_id,
        notification_type="ORDER_PLACED",
        title="Order Placed",
        message="Your order has been placed successfully.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification is not None
    assert notification.customer_id == customer_id
    assert notification.order_id == order_id
    assert notification.notification_type == "ORDER_PLACED"
    assert notification.title == "Order Placed"
    assert notification.is_read is False

    db.close()


# ============================================================
# GET NOTIFICATIONS
# ============================================================

def test_get_notifications():
    _, customer_id, token = create_user(
        prefix="get_notifications"
    )

    order_id = create_order(customer_id)

    create_notification(
        customer_id,
        order_id,
        "ORDER_PLACED",
        "Order Placed",
        "Your order has been placed.",
    )

    create_notification(
        customer_id,
        order_id,
        "PAYMENT_SUCCESS",
        "Payment Successful",
        "Your payment was successful.",
    )

    response = client.get(
        "/api/v1/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 2
    assert all(
        item["customer_id"] == customer_id
        for item in data
    )


def test_get_unread_notifications():
    _, customer_id, token = create_user(
        prefix="get_unread_notifications"
    )

    order_id = create_order(customer_id)

    unread_id = create_notification(
        customer_id,
        order_id,
        "ORDER_PLACED",
        "Order Placed",
        "Your order has been placed.",
    )

    read_id = create_notification(
        customer_id,
        order_id,
        "PAYMENT_SUCCESS",
        "Payment Successful",
        "Your payment was successful.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == read_id)
        .first()
    )

    notification.is_read = True

    db.commit()
    db.close()

    response = client.get(
        "/api/v1/notifications/unread",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == unread_id
        for item in data
    )

    assert all(
        item["is_read"] is False
        for item in data
    )


# ============================================================
# MARK AS READ
# ============================================================

def test_mark_notification_as_read():
    _, customer_id, token = create_user(
        prefix="mark_notification_read"
    )

    order_id = create_order(customer_id)

    notification_id = create_notification(
        customer_id,
        order_id,
    )

    response = client.put(
        f"/api/v1/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["notification_id"] == notification_id
    assert data["is_read"] is True

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.is_read is True

    db.close()


def test_mark_already_read_notification():
    _, customer_id, token = create_user(
        prefix="already_read"
    )

    notification_id = create_notification(
        customer_id=customer_id,
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    notification.is_read = True

    db.commit()
    db.close()

    response = client.put(
        f"/api/v1/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["is_read"] is True


# ============================================================
# NOTIFICATION NOT FOUND
# ============================================================

def test_notification_not_found():
    _, _, token = create_user(
        prefix="notification_not_found"
    )

    response = client.put(
        "/api/v1/notifications/999999/read",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


# ============================================================
# AUTHENTICATION
# ============================================================

def test_notifications_require_authentication():
    response = client.get(
        "/api/v1/notifications"
    )

    assert response.status_code in (401, 403)


def test_unread_notifications_require_authentication():
    response = client.get(
        "/api/v1/notifications/unread"
    )

    assert response.status_code in (401, 403)


def test_mark_notification_requires_authentication():
    response = client.put(
        "/api/v1/notifications/1/read"
    )

    assert response.status_code in (401, 403)


# ============================================================
# CUSTOMER OWNERSHIP
# ============================================================

def test_customer_cannot_mark_another_customer_notification():
    _, customer_id_1, _ = create_user(
        prefix="notification_customer_one"
    )

    _, customer_id_2, token_2 = create_user(
        prefix="notification_customer_two"
    )

    notification_id = create_notification(
        customer_id=customer_id_1,
    )

    response = client.put(
        f"/api/v1/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {token_2}",
        },
    )

    assert response.status_code == 403


def test_customer_only_sees_own_notifications():
    _, customer_id_1, token_1 = create_user(
        prefix="notification_visibility_one"
    )

    _, customer_id_2, _ = create_user(
        prefix="notification_visibility_two"
    )

    notification_1 = create_notification(
        customer_id=customer_id_1,
        title="Customer One",
        message="Customer one notification",
    )

    notification_2 = create_notification(
        customer_id=customer_id_2,
        title="Customer Two",
        message="Customer two notification",
    )

    response = client.get(
        "/api/v1/notifications",
        headers={
            "Authorization": f"Bearer {token_1}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    ids = [item["id"] for item in data]

    assert notification_1 in ids
    assert notification_2 not in ids


# ============================================================
# ROLE AUTHORIZATION
# ============================================================

def test_admin_cannot_view_notifications():
    _, _, admin_token = create_user(
        role=UserRole.ADMIN,
        prefix="admin_view_notifications",
    )

    response = client.get(
        "/api/v1/notifications",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 403


def test_admin_cannot_view_unread_notifications():
    _, _, admin_token = create_user(
        role=UserRole.ADMIN,
        prefix="admin_unread_notifications",
    )

    response = client.get(
        "/api/v1/notifications/unread",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 403


def test_admin_cannot_mark_notification_read():
    _, customer_id, _ = create_user(
        prefix="notification_admin_target"
    )

    notification_id = create_notification(
        customer_id=customer_id,
    )

    _, _, admin_token = create_user(
        role=UserRole.ADMIN,
        prefix="notification_admin",
    )

    response = client.put(
        f"/api/v1/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 403


# ============================================================
# DEFAULT VALUES
# ============================================================

def test_notification_is_unread_by_default():
    _, customer_id, _ = create_user(
        prefix="default_unread"
    )

    notification_id = create_notification(
        customer_id=customer_id,
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification is not None
    assert notification.is_read is False

    db.close()


def test_notification_created_at():
    _, customer_id, _ = create_user(
        prefix="notification_created_at"
    )

    notification_id = create_notification(
        customer_id=customer_id,
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification is not None
    assert notification.created_at is not None

    db.close()


# ============================================================
# NOTIFICATION TYPES
# ============================================================

def test_order_placed_notification():
    _, customer_id, _ = create_user(
        prefix="order_placed_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="ORDER_PLACED",
        title="Order Placed",
        message="Your order has been placed successfully.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "ORDER_PLACED"

    db.close()


def test_order_accepted_notification():
    _, customer_id, _ = create_user(
        prefix="order_accepted_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="ORDER_ACCEPTED",
        title="Order Accepted",
        message="The restaurant has accepted your order.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "ORDER_ACCEPTED"

    db.close()


def test_food_ready_notification():
    _, customer_id, _ = create_user(
        prefix="food_ready_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="FOOD_READY",
        title="Food Ready",
        message="Your food is ready for pickup.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "FOOD_READY"

    db.close()


def test_driver_assigned_notification():
    _, customer_id, _ = create_user(
        prefix="driver_assigned_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="DRIVER_ASSIGNED",
        title="Driver Assigned",
        message="A delivery partner has been assigned.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "DRIVER_ASSIGNED"

    db.close()


def test_out_for_delivery_notification():
    _, customer_id, _ = create_user(
        prefix="out_delivery_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="OUT_FOR_DELIVERY",
        title="Out for Delivery",
        message="Your order is out for delivery.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "OUT_FOR_DELIVERY"

    db.close()


def test_order_delivered_notification():
    _, customer_id, _ = create_user(
        prefix="order_delivered_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="ORDER_DELIVERED",
        title="Order Delivered",
        message="Your order has been delivered.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "ORDER_DELIVERED"

    db.close()


def test_payment_success_notification():
    _, customer_id, _ = create_user(
        prefix="payment_success_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="PAYMENT_SUCCESS",
        title="Payment Successful",
        message="Your payment was successful.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "PAYMENT_SUCCESS"

    db.close()


def test_refund_processed_notification():
    _, customer_id, _ = create_user(
        prefix="refund_processed_event"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        notification_type="REFUND_PROCESSED",
        title="Refund Processed",
        message="Your refund has been processed successfully.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.notification_type == "REFUND_PROCESSED"

    db.close()


# ============================================================
# ALL EVENT TYPES
# ============================================================

def test_all_notification_types():
    _, customer_id, _ = create_user(
        prefix="all_notification_types"
    )

    notification_types = [
        "ORDER_PLACED",
        "ORDER_ACCEPTED",
        "FOOD_READY",
        "DRIVER_ASSIGNED",
        "OUT_FOR_DELIVERY",
        "ORDER_DELIVERED",
        "PAYMENT_SUCCESS",
        "REFUND_PROCESSED",
    ]

    for notification_type in notification_types:
        notification_id = create_notification(
            customer_id=customer_id,
            notification_type=notification_type,
            title=notification_type,
            message=f"{notification_type} notification",
        )

        assert notification_id is not None

    db = SessionLocal()

    notifications = (
        db.query(Notification)
        .filter(
            Notification.customer_id == customer_id
        )
        .all()
    )

    stored_types = {
        notification.notification_type
        for notification in notifications
    }

    assert set(notification_types).issubset(
        stored_types
    )

    db.close()


# ============================================================
# NOTIFICATION WITHOUT ORDER
# ============================================================

def test_notification_without_order():
    _, customer_id, _ = create_user(
        prefix="notification_without_order"
    )

    notification_id = create_notification(
        customer_id=customer_id,
        order_id=None,
        notification_type="GENERAL",
        title="General Notification",
        message="General notification message.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification is not None
    assert notification.order_id is None
    assert notification.customer_id == customer_id

    db.close()


# ============================================================
# ORDER RELATIONSHIP
# ============================================================

def test_notification_can_reference_order():
    _, customer_id, _ = create_user(
        prefix="notification_order_reference"
    )

    order_id = create_order(customer_id)

    notification_id = create_notification(
        customer_id=customer_id,
        order_id=order_id,
        notification_type="ORDER_PLACED",
        title="Order Placed",
        message="Your order has been placed.",
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    assert notification.order_id == order_id
    assert notification.customer_id == customer_id

    db.close()


# ============================================================
# NOTIFICATION ORDERING
# ============================================================

def test_notifications_are_returned_newest_first():
    _, customer_id, token = create_user(
        prefix="notification_ordering"
    )

    first_id = create_notification(
        customer_id=customer_id,
        notification_type="ORDER_PLACED",
        title="First",
        message="First notification",
    )

    second_id = create_notification(
        customer_id=customer_id,
        notification_type="PAYMENT_SUCCESS",
        title="Second",
        message="Second notification",
    )

    response = client.get(
        "/api/v1/notifications",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    ids = [item["id"] for item in data]

    assert second_id in ids
    assert first_id in ids

    assert ids.index(second_id) < ids.index(first_id)


# ============================================================
# READ / UNREAD COUNTS
# ============================================================

def test_read_notification_not_in_unread_list():
    _, customer_id, token = create_user(
        prefix="read_not_unread"
    )

    notification_id = create_notification(
        customer_id=customer_id,
    )

    db = SessionLocal()

    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .first()
    )

    notification.is_read = True

    db.commit()
    db.close()

    response = client.get(
        "/api/v1/notifications/unread",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    ids = [item["id"] for item in data]

    assert notification_id not in ids


def test_mark_read_changes_unread_status():
    _, customer_id, token = create_user(
        prefix="change_unread_status"
    )

    notification_id = create_notification(
        customer_id=customer_id,
    )

    response = client.put(
        f"/api/v1/notifications/{notification_id}/read",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    unread_response = client.get(
        "/api/v1/notifications/unread",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert unread_response.status_code == 200

    unread_ids = [
        item["id"]
        for item in unread_response.json()
    ]

    assert notification_id not in unread_ids
