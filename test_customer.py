import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models.user import User
from models.customer import Customer
from utils.enums import UserRole
from utils.security import hash_password


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


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ============================================================
# TEST SETUP
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
    full_name="Test Customer",
    phone="9876543210",
    password="Password123",
):
    if email is None:
        email = f"customer_{uuid4().hex[:8]}@test.com"

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
        "phone": phone,
    }


def login_user(email, password):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


# ============================================================
# CREATE CUSTOMER
# ============================================================

def test_create_customer():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "Test Customer",
            "email": user["email"],
            "phone": "9876543210",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Customer"
    assert data["email"] == user["email"]
    assert data["phone"] == "9876543210"


def test_customer_user_id_relationship():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "Relationship Customer",
            "email": user["email"],
            "phone": "9876543211",
        },
    )

    assert response.status_code == 201

    db = TestingSessionLocal()

    customer = (
        db.query(Customer)
        .filter(Customer.email == user["email"])
        .first()
    )

    assert customer is not None
    assert customer.user_id == user["id"]

    db.close()


def test_duplicate_customer_profile_not_allowed():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    payload = {
        "name": "Duplicate Customer",
        "email": user["email"],
        "phone": "9876543212",
    }

    first_response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json=payload,
    )

    assert second_response.status_code == 400

    data = second_response.json()

    assert "detail" in data
    assert "already exists" in data["detail"].lower()


# ============================================================
# DUPLICATE EMAIL
# ============================================================

def test_duplicate_customer_email_not_allowed():
    user1 = create_user(
        email="customer1@test.com",
        full_name="Customer One",
        phone="9876543213",
    )

    user2 = create_user(
        email="customer2@test.com",
        full_name="Customer Two",
        phone="9876543214",
    )

    token1 = login_user(
        user1["email"],
        user1["password"],
    )

    response1 = client.post(
        "/api/v1/customers",
        headers=auth_headers(token1),
        json={
            "name": "Customer One",
            "email": "duplicate@test.com",
            "phone": "9876543213",
        },
    )

    assert response1.status_code == 201

    token2 = login_user(
        user2["email"],
        user2["password"],
    )

    response2 = client.post(
        "/api/v1/customers",
        headers=auth_headers(token2),
        json={
            "name": "Customer Two",
            "email": "duplicate@test.com",
            "phone": "9876543214",
        },
    )

    assert response2.status_code == 400

    data = response2.json()

    assert "detail" in data
    assert "email already exists" in data["detail"].lower()


# ============================================================
# GET CUSTOMER
# ============================================================

def test_get_customer():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    create_response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "Get Customer",
            "email": user["email"],
            "phone": "9876543215",
        },
    )

    assert create_response.status_code == 201

    customer_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/customers/{customer_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id
    assert data["name"] == "Get Customer"


def test_get_customer_not_found():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.get(
        "/api/v1/customers/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert "customer not found" in data["detail"].lower()


# ============================================================
# VALIDATION
# ============================================================

def test_customer_invalid_email():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "Invalid Email",
            "email": "invalid-email",
            "phone": "9876543216",
        },
    )

    assert response.status_code == 422


def test_customer_invalid_phone():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "Invalid Phone",
            "email": user["email"],
            "phone": "abcdefghij",
        },
    )

    assert response.status_code == 422


def test_customer_short_name():
    user = create_user()

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "A",
            "email": user["email"],
            "phone": "9876543217",
        },
    )

    assert response.status_code == 422


# ============================================================
# AUTHORIZATION
# ============================================================

def test_customer_create_requires_authentication():
    response = client.post(
        "/api/v1/customers",
        json={
            "name": "No Auth",
            "email": "noauth@test.com",
            "phone": "9876543218",
        },
    )

    assert response.status_code == 401


def test_admin_can_create_customer():
    admin = create_user(
        role=UserRole.ADMIN,
        email="admin@test.com",
        full_name="Admin User",
        phone="9876543220",
    )

    token = login_user(
        admin["email"],
        admin["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "Admin Customer",
            "email": "admincustomer@test.com",
            "phone": "9876543221",
        },
    )

    assert response.status_code == 201


def test_delivery_partner_cannot_create_customer():
    user = create_user(
        role=UserRole.DELIVERY_PARTNER,
        email="driver@test.com",
        full_name="Delivery Driver",
        phone="9876543222",
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": "Forbidden Customer",
            "email": "forbidden@test.com",
            "phone": "9876543223",
        },
    )

    assert response.status_code == 403