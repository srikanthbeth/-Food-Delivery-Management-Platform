
import os
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from main import app
from models.address import Address
from models.cart import Cart
from models.cart_item import CartItem
from models.customer import Customer
from models.menu_item import MenuItem
from models.order import Order
from models.payment import Payment
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


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
# ============================================================
# HELPERS
# ============================================================

def unique_email(prefix="payment"):
    prefix = prefix.replace(" ", "_").lower()
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def create_user_and_login(role: UserRole):
    db = SessionLocal()

    email = unique_email(role.value)

    user = User(
        full_name=f"Payment {role.value}",
        email=email,
        phone=f"8{uuid4().int % 10**9:09d}",
        password_hash=hash_password("Test@12345"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.flush()

    customer_id = None

    if role == UserRole.CUSTOMER:
        customer = Customer(
            user_id=user.id,
            name=f"Payment Customer {uuid4().hex[:8]}",
            email=email,
            phone=user.phone,
        )

        db.add(customer)
        db.flush()

        customer_id = customer.id

    user_id = user.id

    db.commit()
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

    return customer_id, token, user_id


def create_order(
    customer_id: int,
    total_amount=Decimal("145.00"),
    order_status=OrderStatus.PENDING,
):
    db = SessionLocal()

    # Create restaurant owner
    owner_email = unique_email("restaurant_owner")

    owner = User(
        full_name="Payment Restaurant Owner",
        email=owner_email,
        phone=f"7{uuid4().int % 10**9:09d}",
        password_hash=hash_password("Test@12345"),
        role=UserRole.RESTAURANT_OWNER,
        is_active=True,
    )

    db.add(owner)
    db.flush()

    # Create restaurant
    restaurant = Restaurant(
        restaurant_name=f"Payment Restaurant {uuid4().hex[:8]}",
        owner_id=owner.id,
        address="100 Payment Street",
        city="Hyderabad",
        phone=f"6{uuid4().int % 10**9:09d}",
        cuisine_type="Indian",
        opening_time="09:00",
        closing_time="23:00",
        status=RestaurantStatus.OPEN,
        delivery_radius=10,
    )

    db.add(restaurant)
    db.flush()

    # Create address belonging to the customer
    address = Address(
        customer_id=customer_id,
        address_line="10 Payment Road",
        city="Hyderabad",
        pincode="500001",
        latitude=17.3850,
        longitude=78.4867,
        address_type="Home",
        is_default=True,
    )

    db.add(address)
    db.flush()

    # Create order directly
    order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant.id,
        address_id=address.id,
        subtotal=Decimal("100.00"),
        delivery_fee=Decimal("40.00"),
        discount=Decimal("0.00"),
        tax=Decimal("5.00"),
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


def create_payment_directly(
    order_id: int,
    amount=Decimal("145.00"),
    transaction_id=None,
    payment_method=PaymentMethod.UPI,
    payment_status=PaymentTransactionStatus.SUCCESSFUL,
):
    db = SessionLocal()

    if transaction_id is None:
        transaction_id = f"TXN_{uuid4().hex[:12]}"

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
    db = SessionLocal()

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    db.refresh(order)

    db.close()

    return order


def payment_payload(
    amount="145.00",
    payment_method="UPI",
    transaction_id=None,
):
    if transaction_id is None:
        transaction_id = f"TXN_{uuid4().hex[:12]}"

    return {
        "amount": amount,
        "payment_method": payment_method,
        "transaction_id": transaction_id,
    }


# ============================================================
# AUTHENTICATION
# ============================================================

def test_create_payment_requires_authentication():

    response = client.post(
        "/api/v1/payments/1",
        json=payment_payload(),
    )

    assert response.status_code == 401


def test_get_payment_requires_authentication():

    response = client.get(
        "/api/v1/payments/1",
    )

    assert response.status_code == 401


def test_get_order_payment_requires_authentication():

    response = client.get(
        "/api/v1/orders/1/payment",
    )

    assert response.status_code == 401


# ============================================================
# CREATE PAYMENT
# ============================================================

def test_create_payment():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order_id"] == order_id
    assert Decimal(str(data["amount"])) == Decimal("145.00")
    assert data["payment_method"] == "UPI"
    assert data["payment_status"] == "Successful"
    assert data["transaction_id"]


def test_payment_order_not_found():

    _, token, _ = create_user_and_login(
        UserRole.ADMIN
    )

    response = client.post(
        "/api/v1/payments/999999",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_payment_amount_mismatch():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            amount="100.00"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400


def test_cancelled_order_cannot_be_paid():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id,
        order_status=OrderStatus.CANCELLED,
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400


# ============================================================
# DUPLICATE PAYMENT / TRANSACTION
# ============================================================

def test_duplicate_transaction_id():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_1 = create_order(
        customer_id=customer_id
    )

    order_2 = create_order(
        customer_id=customer_id
    )

    transaction_id = f"TXN_{uuid4().hex[:12]}"

    response_1 = client.post(
        f"/api/v1/payments/{order_1}",
        json=payment_payload(
            transaction_id=transaction_id
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response_1.status_code == 201

    response_2 = client.post(
        f"/api/v1/payments/{order_2}",
        json=payment_payload(
            transaction_id=transaction_id
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response_2.status_code == 400


def test_duplicate_payment_for_same_order():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response_1 = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response_1.status_code == 201

    response_2 = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response_2.status_code == 400


# ============================================================
# CUSTOMER OWNERSHIP
# ============================================================

def test_customer_can_pay_own_order():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201


def test_customer_cannot_pay_another_customer_order():

    customer_1, token_1, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    customer_2, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_2
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token_1}"
        },
    )

    assert response.status_code == 403


def test_admin_can_pay_any_order():

    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, admin_token, _ = create_user_and_login(
        UserRole.ADMIN
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 201


# ============================================================
# ORDER PAYMENT STATUS
# ============================================================

def test_successful_payment_updates_order_payment_status():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    db = SessionLocal()

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    assert order.payment_status == PaymentStatus.PAID

    db.close()


# ============================================================
# GET PAYMENT
# ============================================================

def test_get_payment_by_id():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    payment_id = create_payment_directly(
        order_id=order_id
    )

    response = client.get(
        f"/api/v1/payments/{payment_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == payment_id
    assert data["order_id"] == order_id


def test_get_payment_not_found():

    _, token, _ = create_user_and_login(
        UserRole.ADMIN
    )

    response = client.get(
        "/api/v1/payments/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_get_order_payment():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    create_payment_directly(
        order_id=order_id
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/payment",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_id"] == order_id


def test_order_payment_not_found():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.get(
        f"/api/v1/orders/{order_id}/payment",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


# ============================================================
# VALIDATION
# ============================================================

def test_invalid_payment_method():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            payment_method="Bitcoin"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_zero_amount_rejected():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            amount="0.00"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_negative_amount_rejected():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            amount="-10.00"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_empty_transaction_id_rejected():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json={
            "amount": "145.00",
            "payment_method": "UPI",
            "transaction_id": "",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_transaction_id_whitespace_rejected():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json={
            "amount": "145.00",
            "payment_method": "UPI",
            "transaction_id": "   ",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


# ============================================================
# PAYMENT METHODS
# ============================================================

def test_upi_payment():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            payment_method="UPI"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "UPI"


def test_card_payment():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            payment_method="Card"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "Card"


def test_wallet_payment():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            payment_method="Wallet"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "Wallet"


def test_cash_on_delivery_payment():

    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    order_id = create_order(
        customer_id=customer_id
    )

    response = client.post(
        f"/api/v1/payments/{order_id}",
        json=payment_payload(
            payment_method="Cash on Delivery"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201
    assert response.json()["payment_method"] == "Cash on Delivery"

