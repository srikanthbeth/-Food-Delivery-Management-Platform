import os
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

os.environ["TEST_DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from database import Base
from main import app
from models.user import User
from utils.enums import UserRole
from utils.security import hash_password


TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
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


# ============================================================
# HELPERS
# ============================================================

def create_user(
    role=UserRole.CUSTOMER,
    email=None,
    full_name="Test User",
    phone="9876543210",
):

    from database import SessionLocal

    if email is None:
        email = (
            f"user_{uuid4().hex[:8]}"
            "@test.com"
        )

    db = SessionLocal()

    user = User(
        full_name=full_name,
        email=email,
        phone=phone,
        password_hash=hash_password(
            "Password123"
        ),
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
        "password": "Password123",
    }


def get_token(user):

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

    token = get_token(user)

    return {
        "Authorization": f"Bearer {token}"
    }


def create_admin():

    return create_user(
        role=UserRole.ADMIN
    )


def create_customer():

    return create_user(
        role=UserRole.CUSTOMER
    )


def create_coupon(
    admin,
    coupon_code=None,
    discount_type="Percentage",
    discount_value="10",
    minimum_order_value="500",
    maximum_discount="100",
    start_date=None,
    expiry_date=None,
    usage_limit=10,
    status=True,
):

    if coupon_code is None:
        coupon_code = (
            f"SAVE{uuid4().hex[:6].upper()}"
        )

    if start_date is None:
        start_date = date.today().isoformat()

    if expiry_date is None:
        expiry_date = (
            date.today()
            + timedelta(days=30)
        ).isoformat()

    payload = {
        "coupon_code": coupon_code,
        "discount_type": discount_type,
        "discount_value": discount_value,
        "minimum_order_value": minimum_order_value,
        "maximum_discount": maximum_discount,
        "start_date": start_date,
        "expiry_date": expiry_date,
        "usage_limit": usage_limit,
        "status": status,
    }

    response = client.post(
        "/api/v1/coupons",
        json=payload,
        headers=auth_headers(admin),
    )

    return response


# ============================================================
# CREATE COUPON TESTS
# ============================================================

def test_admin_can_create_coupon():

    admin = create_admin()

    response = create_coupon(admin)

    assert response.status_code == 201

    data = response.json()

    assert data["coupon_code"].startswith(
        "SAVE"
    )

    assert data["discount_type"] == "Percentage"
    assert float(data["discount_value"]) == 10
    assert data["usage_count"] == 0


def test_customer_cannot_create_coupon():

    customer = create_customer()

    response = client.post(
        "/api/v1/coupons",
        json={
            "coupon_code": "CUSTOMER10",
            "discount_type": "Percentage",
            "discount_value": "10",
            "minimum_order_value": "100",
            "maximum_discount": "50",
            "start_date": date.today().isoformat(),
            "expiry_date": (
                date.today()
                + timedelta(days=30)
            ).isoformat(),
            "usage_limit": 10,
            "status": True,
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 403


def test_coupon_code_must_be_unique():

    admin = create_admin()

    code = (
        f"DUP{uuid4().hex[:6].upper()}"
    )

    first = create_coupon(
        admin,
        coupon_code=code,
    )

    assert first.status_code == 201

    second = create_coupon(
        admin,
        coupon_code=code,
    )

    assert second.status_code == 400


def test_invalid_discount_type_rejected():

    admin = create_admin()

    response = create_coupon(
        admin,
        discount_type="Invalid",
    )

    assert response.status_code == 422


def test_percentage_discount_above_100_rejected():

    admin = create_admin()

    response = create_coupon(
        admin,
        discount_type="Percentage",
        discount_value="101",
    )

    assert response.status_code == 422


def test_zero_discount_rejected():

    admin = create_admin()

    response = create_coupon(
        admin,
        discount_value="0",
    )

    assert response.status_code == 422


def test_negative_discount_rejected():

    admin = create_admin()

    response = create_coupon(
        admin,
        discount_value="-10",
    )

    assert response.status_code == 422


def test_invalid_date_range_rejected():

    admin = create_admin()

    response = create_coupon(
        admin,
        start_date="2026-12-31",
        expiry_date="2026-01-01",
    )

    assert response.status_code == 422


def test_fixed_coupon_cannot_have_maximum_discount():

    admin = create_admin()

    response = create_coupon(
        admin,
        discount_type="Fixed",
        discount_value="100",
        maximum_discount="50",
    )

    assert response.status_code == 422


# ============================================================
# GET COUPON TESTS
# ============================================================

def test_admin_can_get_coupons():

    admin = create_admin()

    create_coupon(admin)

    response = client.get(
        "/api/v1/coupons",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list,
    )


def test_customer_cannot_get_coupons():

    customer = create_customer()

    response = client.get(
        "/api/v1/coupons",
        headers=auth_headers(customer),
    )

    assert response.status_code == 403


# ============================================================
# APPLY COUPON TESTS
# ============================================================

def test_percentage_coupon_applies_discount():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"PERCENT{uuid4().hex[:6].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        discount_type="Percentage",
        discount_value="10",
        minimum_order_value="500",
        maximum_discount="100",
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 200

    data = response.json()

    assert float(
        data["discount_amount"]
    ) == 100

    assert float(
        data["final_amount"]
    ) == 900


def test_fixed_coupon_applies_discount():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"FIXED{uuid4().hex[:6].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        discount_type="Fixed",
        discount_value="100",
        minimum_order_value="500",
        maximum_discount=None,
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 200

    data = response.json()

    assert float(
        data["discount_amount"]
    ) == 100

    assert float(
        data["final_amount"]
    ) == 900


def test_coupon_not_found():

    customer = create_customer()

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": "NOTFOUND",
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 404


def test_expired_coupon_cannot_be_applied():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"EXPIRED{uuid4().hex[:5].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        start_date=(
            date.today()
            - timedelta(days=30)
        ).isoformat(),
        expiry_date=(
            date.today()
            - timedelta(days=1)
        ).isoformat(),
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 400


def test_future_coupon_cannot_be_applied():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"FUTURE{uuid4().hex[:4].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        start_date=(
            date.today()
            + timedelta(days=2)
        ).isoformat(),
        expiry_date=(
            date.today()
            + timedelta(days=30)
        ).isoformat(),
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 400


def test_inactive_coupon_cannot_be_applied():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"INACTIVE{uuid4().hex[:4].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        status=False,
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 400


def test_minimum_order_value_required():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"MIN{uuid4().hex[:6].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        minimum_order_value="1000",
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "500",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 400


def test_maximum_discount_is_respected():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"MAX{uuid4().hex[:6].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        discount_type="Percentage",
        discount_value="20",
        minimum_order_value="100",
        maximum_discount="100",
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 200

    data = response.json()

    assert float(
        data["discount_amount"]
    ) == 100

    assert float(
        data["final_amount"]
    ) == 900


def test_usage_limit_enforced():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"LIMIT{uuid4().hex[:5].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
        usage_limit=1,
    )

    first = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert first.status_code == 200

    second = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code,
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert second.status_code == 400


def test_coupon_apply_requires_authentication():

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": "SAVE10",
            "order_amount": "1000",
        },
    )

    assert response.status_code == 401


def test_coupon_code_is_case_insensitive():

    admin = create_admin()
    customer = create_customer()

    code = (
        f"CASE{uuid4().hex[:6].upper()}"
    )

    create_coupon(
        admin,
        coupon_code=code,
    )

    response = client.post(
        "/api/v1/coupons/apply",
        json={
            "coupon_code": code.lower(),
            "order_amount": "1000",
        },
        headers=auth_headers(customer),
    )

    assert response.status_code == 200