
import os
from decimal import Decimal
from uuid import uuid4
from datetime import time

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from main import app

from models.address import Address
from models.customer import Customer
from models.order import Order
from models.payment import Payment
from models.refund import Refund
from models.restaurant import Restaurant
from models.user import User

from utils.enums import (
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    PaymentTransactionStatus,
    RestaurantStatus,
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


def unique_email(prefix="refund"):
    safe_prefix = "".join(
        ch.lower() if ch.isalnum() else "_"
        for ch in prefix
    ).strip("_")

    return f"{safe_prefix}_{uuid4().hex[:10]}@example.com"


def create_user_and_login(role: UserRole):
    db = SessionLocal()

    email = unique_email(role.value)
    phone = f"9{uuid4().int % 10**9:09d}"

    user = User(
        full_name=f"Refund Test {role.value.title()}",
        email=email,
        phone=phone,
        password_hash=hash_password("Test@123"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    customer_id = None

    if role == UserRole.CUSTOMER:
        customer = Customer(
            user_id=user.id,
            name="Refund Test Customer",
            email=email,
            phone=phone,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        customer_id = customer.id

        # Verify customer really exists before closing session
        verified_customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        assert verified_customer is not None, (
            f"Customer {customer_id} was not created"
        )

    user_id = user.id

    db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test@123",
        },
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return customer_id, token, user_id


def create_order(
    customer_id: int,
    order_status: OrderStatus = OrderStatus.PENDING,
    total_amount: Decimal = Decimal("500.00"),
):
    db = SessionLocal()

    # --------------------------------------------------------
    # Verify customer exists
    # --------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    assert customer is not None, (
        f"Customer {customer_id} does not exist"
    )

    # --------------------------------------------------------
    # Create restaurant
    # --------------------------------------------------------

    restaurant_owner = User(
        full_name="Refund Restaurant Owner",
        email=unique_email("restaurant_owner"),
        phone=f"8{uuid4().int % 10**9:09d}",
        password_hash=hash_password("Test@123"),
        role=UserRole.RESTAURANT_OWNER,
        is_active=True,
    )

    db.add(restaurant_owner)
    db.commit()
    db.refresh(restaurant_owner)

    restaurant = Restaurant(
        restaurant_name=f"Refund Restaurant {uuid4().hex[:6]}",
        owner_id=restaurant_owner.id,
        address="123 Restaurant Street",
        city="Hyderabad",
        phone="9876543210",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(23, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # --------------------------------------------------------
    # Create address
    # --------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="123 Test Street",
        city="Hyderabad",
        pincode="500001",
        address_type="Home",
        is_default=True,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # --------------------------------------------------------
    # Create order
    # --------------------------------------------------------

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        delivery_partner_id=None,
        subtotal=total_amount,
        delivery_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        total_amount=total_amount,
        order_status=order_status,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    order_id = order.id

    db.close()

    return order_id



def create_order(
    customer_id,
    total_amount=Decimal("145.00"),
    order_status=OrderStatus.PENDING,
):
    db = SessionLocal()

    # --------------------------------------------------------
    # Verify customer exists
    # --------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    assert customer is not None, (
        f"Customer {customer_id} does not exist"
    )

    # --------------------------------------------------------
    # Create restaurant owner
    # --------------------------------------------------------

    owner_email = unique_email("restaurant_owner")

    owner = User(
        full_name="Refund Test Restaurant Owner",
        email=owner_email,
        phone=f"9{uuid4().int % 10**9:09d}",
        password_hash=hash_password("Test@123"),
        role=UserRole.RESTAURANT_OWNER,
        is_active=True,
    )

    db.add(owner)
    db.commit()
    db.refresh(owner)

    # --------------------------------------------------------
    # Create restaurant
    # --------------------------------------------------------

    restaurant = Restaurant(
        restaurant_name=f"Refund Restaurant {uuid4().hex[:6]}",
        owner_id=owner.id,
        address="Test Address",
        city="Hyderabad",
        phone="9876543210",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(23, 0),
        status=RestaurantStatus.OPEN,
        delivery_radius=10,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    # --------------------------------------------------------
    # Create customer address
    # --------------------------------------------------------

    address = Address(
        customer_id=customer.id,
        address_line="Test Customer Address",
        city="Hyderabad",
        pincode="500001",
        latitude=Decimal("17.385044"),
        longitude=Decimal("78.486671"),
        address_type="Home",
        is_default=True,
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    # --------------------------------------------------------
    # Create order
    # --------------------------------------------------------

    delivery_fee = Decimal("20.00")
    discount = Decimal("0.00")
    tax = Decimal("0.00")

    subtotal = total_amount - delivery_fee + discount - tax

    if subtotal < Decimal("0.00"):
        subtotal = Decimal("0.00")

    order = Order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        delivery_partner_id=None,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        discount=discount,
        tax=tax,
        total_amount=total_amount,
        order_status=order_status,
        payment_status=PaymentStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    order_id = order.id

    db.close()

    # IMPORTANT:
    # Always return the actual database order ID.
    return order_id


def create_payment_directly(
    order_id: int,
    amount=Decimal("145.00"),
    transaction_id=None,
    payment_method=PaymentMethod.UPI,
    payment_status=PaymentTransactionStatus.SUCCESSFUL,
):
    db: Session = SessionLocal()

    if transaction_id is None:
        transaction_id = f"PAY-{uuid4().hex[:12]}"

    payment = Payment(
        order_id=order_id,
        amount=amount,
        payment_method=payment_method,
        transaction_id=transaction_id,
        payment_status=payment_status,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    payment_id = payment.id

    db.close()

    return payment_id


def get_order_from_db(order_id: int):
    db: Session = SessionLocal()

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    db.close()

    return order


def get_payment_from_db(payment_id: int):
    db: Session = SessionLocal()

    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    db.close()

    return payment


def get_refund_from_db(refund_id: int):
    db: Session = SessionLocal()

    refund = (
        db.query(Refund)
        .filter(Refund.id == refund_id)
        .first()
    )

    db.close()

    return refund


def refund_payload(
    amount="145.00",
    reason="Order cancelled by customer",
    refund_transaction_id=None,
):
    if refund_transaction_id is None:
        refund_transaction_id = f"REF-{uuid4().hex[:12]}"

    return {
        "amount": amount,
        "reason": reason,
        "refund_transaction_id": refund_transaction_id,
    }


# ============================================================
# AUTHENTICATION
# ============================================================

def test_cancel_order_requires_authentication():
    _, _, customer_id = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(customer_id)

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel"
    )

    assert response.status_code == 401


def test_create_refund_requires_authentication():
    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(
        order_id
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        json=refund_payload(),
    )

    assert response.status_code in (401, 403), response.text




def test_get_refunds_requires_authentication():
    response = client.get("/api/v1/refunds")

    assert response.status_code == 401


# ============================================================
# ORDER CANCELLATION
# ============================================================

def test_customer_can_cancel_pending_order():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.PENDING,
    )

    assert order_id is not None

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Order cancelled successfully"
    assert data["order_id"] == order_id
    assert data["order_status"] == "Cancelled"

    order = get_order_from_db(order_id)

    assert order is not None
    assert order.order_status == OrderStatus.CANCELLED


def test_customer_can_cancel_accepted_order():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.ACCEPTED,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["order_status"] == "Cancelled"


def test_customer_can_cancel_preparing_order():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.PREPARING,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["order_status"] == "Cancelled"


def test_ready_order_cannot_be_cancelled():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.READY,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "cannot be cancelled" in response.json()["detail"].lower()


def test_picked_up_order_cannot_be_cancelled():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.PICKED_UP,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "cannot be cancelled" in response.json()["detail"].lower()


def test_out_for_delivery_order_cannot_be_cancelled():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.OUT_FOR_DELIVERY,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "cannot be cancelled" in response.json()["detail"].lower()


def test_delivered_order_cannot_be_cancelled():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.DELIVERED,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "delivered" in response.json()["detail"].lower()


def test_already_cancelled_order_cannot_be_cancelled():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "already cancelled" in response.json()["detail"].lower()


def test_cancel_order_not_found():
    _, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    response = client.post(
        "/api/v1/orders/999999/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404
    assert "order not found" in response.json()["detail"].lower()


# ============================================================
# CUSTOMER OWNERSHIP
# ============================================================

def test_customer_cannot_cancel_another_customer_order():
    customer1_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, token2, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer1_id,
        order_status=OrderStatus.PENDING,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token2}"
        },
    )

    assert response.status_code == 403, response.text


def test_customer_cannot_refund_another_customer_payment():
    customer1_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, token2, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer1_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token2}"
        },
        json=refund_payload(),
    )

    assert response.status_code == 403, response.text


# ============================================================
# ROLE AUTHORIZATION
# ============================================================

def test_non_customer_cannot_cancel_order():
    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, token, _ = create_user_and_login(
        UserRole.DELIVERY_PARTNER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.PENDING,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403, response.text


def test_non_customer_cannot_create_refund():
    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, token, _ = create_user_and_login(
        UserRole.DELIVERY_PARTNER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(),
    )

    assert response.status_code == 403, response.text


def test_non_customer_cannot_get_refunds():
    _, token, _ = create_user_and_login(
        UserRole.DELIVERY_PARTNER
    )

    response = client.get(
        "/api/v1/refunds",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403, response.text


# ============================================================
# ADMIN CANCELLATION
# ============================================================

def test_admin_can_cancel_any_order():
    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token, _ = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.PENDING,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["success"] is True
    assert data["order_id"] == order_id
    assert data["order_status"] == "Cancelled"


# ============================================================
# CREATE REFUND
# ============================================================

def test_customer_can_create_full_refund_after_cancellation():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        total_amount=Decimal("145.00"),
        order_status=OrderStatus.PENDING,
    )

    payment_id = create_payment_directly(
        order_id,
        amount=Decimal("145.00"),
    )

    cancel_response = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert cancel_response.status_code == 200, cancel_response.text

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="145.00"
        ),
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["payment_id"] == payment_id
    assert data["order_id"] == order_id
    assert Decimal(data["amount"]) == Decimal("145.00")
    assert data["reason"] == "Order cancelled by customer"
    assert data["refund_status"] == "Refunded"
    assert data["refund_transaction_id"].startswith("REF-")
    assert data["refunded_at"] is not None
    assert data["created_at"] is not None


def test_full_refund_updates_payment_status():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        total_amount=Decimal("145.00"),
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(
        order_id,
        amount=Decimal("145.00"),
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="145.00"
        ),
    )

    assert response.status_code == 201, response.text

    payment = get_payment_from_db(payment_id)
    order = get_order_from_db(order_id)

    assert payment.payment_status == PaymentTransactionStatus.REFUNDED
    assert order.payment_status == PaymentStatus.REFUNDED


def test_partial_refund_does_not_mark_payment_fully_refunded():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        total_amount=Decimal("145.00"),
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(
        order_id,
        amount=Decimal("145.00"),
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="50.00"
        ),
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert Decimal(data["amount"]) == Decimal("50.00")
    assert data["refund_status"] == "Refunded"

    payment = get_payment_from_db(payment_id)
    order = get_order_from_db(order_id)

    assert payment.payment_status == PaymentTransactionStatus.SUCCESSFUL
    assert order.payment_status != PaymentStatus.REFUNDED


def test_admin_can_create_refund():
    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token, _ = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json=refund_payload(),
    )

    assert response.status_code == 201, response.text


# ============================================================
# REFUND BUSINESS RULES
# ============================================================

def test_refund_payment_not_found():
    _, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    response = client.post(
        "/api/v1/payments/999999/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(),
    )

    assert response.status_code == 404
    assert "payment not found" in response.json()["detail"].lower()


def test_refund_requires_successful_payment():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(
        order_id,
        payment_status=PaymentTransactionStatus.FAILED,
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(),
    )

    assert response.status_code == 400
    assert "successful payments" in response.json()["detail"].lower()


def test_refund_requires_cancelled_order():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.PENDING,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(),
    )

    assert response.status_code == 400
    assert "cancelled" in response.json()["detail"].lower()


def test_duplicate_refund_for_same_payment_not_allowed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    first_response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="50.00"
        ),
    )

    assert first_response.status_code == 201, first_response.text

    second_response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="40.00"
        ),
    )

    assert second_response.status_code == 400
    assert "refund already exists" in (
        second_response.json()["detail"].lower()
    )


def test_duplicate_refund_transaction_id_not_allowed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order1_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment1_id = create_payment_directly(order1_id)

    transaction_id = f"REF-{uuid4().hex[:12]}"

    first_response = client.post(
        f"/api/v1/payments/{payment1_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="50.00",
            refund_transaction_id=transaction_id,
        ),
    )

    assert first_response.status_code == 201, first_response.text

    order2_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment2_id = create_payment_directly(order2_id)

    second_response = client.post(
        f"/api/v1/payments/{payment2_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="40.00",
            refund_transaction_id=transaction_id,
        ),
    )

    assert second_response.status_code == 400
    assert "transaction id already exists" in (
        second_response.json()["detail"].lower()
    )


def test_refund_amount_cannot_exceed_payment_amount():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        total_amount=Decimal("145.00"),
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(
        order_id,
        amount=Decimal("145.00"),
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="200.00"
        ),
    )

    assert response.status_code == 400
    assert "cannot exceed" in response.json()["detail"].lower()


# ============================================================
# REFUND VALIDATION
# ============================================================

def test_refund_amount_cannot_be_zero():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="0.00"
        ),
    )

    assert response.status_code == 422


def test_refund_amount_cannot_be_negative():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="-10.00"
        ),
    )

    assert response.status_code == 422


def test_refund_reason_cannot_be_too_short():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            reason="ab"
        ),
    )

    assert response.status_code == 422


def test_refund_reason_cannot_be_empty():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            reason=""
        ),
    )

    assert response.status_code == 422


def test_refund_reason_cannot_be_whitespace():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            reason="   "
        ),
    )

    assert response.status_code == 422


def test_refund_transaction_id_cannot_be_too_short():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            refund_transaction_id="ab"
        ),
    )

    assert response.status_code == 422


def test_refund_transaction_id_cannot_be_empty():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            refund_transaction_id=""
        ),
    )

    assert response.status_code == 422


def test_refund_transaction_id_cannot_be_whitespace():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            refund_transaction_id="   "
        ),
    )

    assert response.status_code == 422


# ============================================================
# GET REFUNDS
# ============================================================

def test_customer_can_get_own_refunds():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    create_response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(),
    )

    assert create_response.status_code == 201, create_response.text

    response = client.get(
        "/api/v1/refunds",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        refund["payment_id"] == payment_id
        for refund in data
    )


def test_customer_only_sees_own_refunds():
    customer1_id, token1, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    customer2_id, token2, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order1_id = create_order(
        customer1_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment1_id = create_payment_directly(order1_id)

    response1 = client.post(
        f"/api/v1/payments/{payment1_id}/refund",
        headers={
            "Authorization": f"Bearer {token1}"
        },
        json=refund_payload(),
    )

    assert response1.status_code == 201, response1.text

    order2_id = create_order(
        customer2_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment2_id = create_payment_directly(order2_id)

    response2 = client.post(
        f"/api/v1/payments/{payment2_id}/refund",
        headers={
            "Authorization": f"Bearer {token2}"
        },
        json=refund_payload(),
    )

    assert response2.status_code == 201, response2.text

    response = client.get(
        "/api/v1/refunds",
        headers={
            "Authorization": f"Bearer {token1}"
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    payment_ids = [
        refund["payment_id"]
        for refund in data
    ]

    assert payment1_id in payment_ids
    assert payment2_id not in payment_ids


def test_admin_can_get_all_refunds():
    customer1_id, token1, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    customer2_id, token2, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token, _ = create_user_and_login(
        UserRole.ADMIN
    )

    order1_id = create_order(
        customer1_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment1_id = create_payment_directly(order1_id)

    response1 = client.post(
        f"/api/v1/payments/{payment1_id}/refund",
        headers={
            "Authorization": f"Bearer {token1}"
        },
        json=refund_payload(),
    )

    assert response1.status_code == 201, response1.text

    order2_id = create_order(
        customer2_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment2_id = create_payment_directly(order2_id)

    response2 = client.post(
        f"/api/v1/payments/{payment2_id}/refund",
        headers={
            "Authorization": f"Bearer {token2}"
        },
        json=refund_payload(),
    )

    assert response2.status_code == 201, response2.text

    response = client.get(
        "/api/v1/refunds",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    payment_ids = [
        refund["payment_id"]
        for refund in data
    ]

    assert payment1_id in payment_ids
    assert payment2_id in payment_ids


# ============================================================
# REFUND RESPONSE / DATABASE
# ============================================================

def test_refund_is_saved_in_database():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        total_amount=Decimal("145.00"),
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(
        order_id,
        amount=Decimal("145.00"),
    )

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            amount="100.00",
            reason="Customer requested cancellation",
        ),
    )

    assert response.status_code == 201, response.text

    refund_id = response.json()["id"]

    refund = get_refund_from_db(refund_id)

    assert refund is not None
    assert refund.payment_id == payment_id
    assert refund.order_id == order_id
    assert refund.amount == Decimal("100.00")
    assert refund.reason == "Customer requested cancellation"
    assert refund.refund_status == PaymentTransactionStatus.REFUNDED
    assert refund.refunded_at is not None


def test_refund_reason_is_trimmed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            reason="   Customer cancelled order   "
        ),
    )

    assert response.status_code == 201, response.text

    assert response.json()["reason"] == (
        "Customer cancelled order"
    )


def test_refund_transaction_id_is_trimmed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    payment_id = create_payment_directly(order_id)

    response = client.post(
        f"/api/v1/payments/{payment_id}/refund",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=refund_payload(
            refund_transaction_id="   REF-TRIM-001   "
        ),
    )

    assert response.status_code == 201, response.text

    assert response.json()["refund_transaction_id"] == (
        "REF-TRIM-001"
    )
