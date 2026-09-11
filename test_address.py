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
from models.address import Address
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


def create_customer(user):
    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.post(
        "/api/v1/customers",
        headers=auth_headers(token),
        json={
            "name": user["email"].split("@")[0],
            "email": user["email"],
            "phone": user["phone"] if "phone" in user else "9876543210",
        },
    )

    assert response.status_code == 201

    return response.json(), token


def address_payload(
    address_line="123 Main Street",
    city="Hyderabad",
    pincode="500001",
    address_type="Home",
    is_default=False,
):
    return {
        "address_line": address_line,
        "city": city,
        "pincode": pincode,
        "latitude": 17.385044,
        "longitude": 78.486671,
        "address_type": address_type,
        "is_default": is_default,
    }


# ============================================================
# CREATE ADDRESS
# ============================================================

def test_create_address():
    user = create_user(
        email="address1@test.com",
        full_name="Address User",
        phone="9876543230",
    )

    customer, token = create_customer(user)

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer["id"]
    assert data["address_line"] == "123 Main Street"
    assert data["city"] == "Hyderabad"
    assert data["pincode"] == "500001"


def test_first_address_becomes_default():
    user = create_user(
        email="default1@test.com",
        full_name="Default User",
        phone="9876543231",
    )

    customer, token = create_customer(user)

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(
            is_default=False,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["is_default"] is True


def test_second_default_address_unsets_previous_default():
    user = create_user(
        email="default2@test.com",
        full_name="Default User Two",
        phone="9876543232",
    )

    customer, token = create_customer(user)

    first = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(
            address_line="First Address",
            is_default=True,
        ),
    )

    assert first.status_code == 201

    first_id = first.json()["id"]

    second = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(
            address_line="Second Address",
            is_default=True,
        ),
    )

    assert second.status_code == 201

    second_data = second.json()

    assert second_data["is_default"] is True

    db = TestingSessionLocal()

    first_address = (
        db.query(Address)
        .filter(Address.id == first_id)
        .first()
    )

    assert first_address.is_default is False

    db.close()


# ============================================================
# GET ADDRESSES
# ============================================================

def test_get_customer_addresses():
    user = create_user(
        email="getaddress@test.com",
        full_name="Get Address",
        phone="9876543233",
    )

    customer, token = create_customer(user)

    client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(),
    )

    response = client.get(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["customer_id"] == customer["id"]


def test_get_addresses_customer_not_found():
    user = create_user(
        email="notfoundaddress@test.com",
        full_name="Not Found",
        phone="9876543234",
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.get(
        "/api/v1/customers/999999/addresses",
        headers=auth_headers(token),
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert "customer not found" in data["detail"].lower()


# ============================================================
# UPDATE ADDRESS
# ============================================================

def test_update_address():
    user = create_user(
        email="updateaddress@test.com",
        full_name="Update Address",
        phone="9876543235",
    )

    customer, token = create_customer(user)

    create_response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(),
    )

    assert create_response.status_code == 201

    address_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/addresses/{address_id}",
        headers=auth_headers(token),
        json={
            "address_line": "Updated Street",
            "city": "Bengaluru",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["address_line"] == "Updated Street"
    assert data["city"] == "Bengaluru"


def test_update_address_not_found():
    user = create_user(
        email="update404@test.com",
        full_name="Update Not Found",
        phone="9876543236",
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    response = client.put(
        "/api/v1/addresses/999999",
        headers=auth_headers(token),
        json={
            "city": "Hyderabad",
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert "address not found" in data["detail"].lower()


# ============================================================
# CUSTOMER OWNERSHIP
# ============================================================

def test_customer_cannot_access_other_customer_addresses():
    user1 = create_user(
        email="owner1@test.com",
        full_name="Owner One",
        phone="9876543237",
    )

    customer1, token1 = create_customer(user1)

    create_response = client.post(
        f"/api/v1/customers/{customer1['id']}/addresses",
        headers=auth_headers(token1),
        json=address_payload(),
    )

    assert create_response.status_code == 201

    user2 = create_user(
        email="owner2@test.com",
        full_name="Owner Two",
        phone="9876543238",
    )

    customer2, token2 = create_customer(user2)

    response = client.get(
        f"/api/v1/customers/{customer1['id']}/addresses",
        headers=auth_headers(token2),
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data
    assert "own addresses" in data["detail"].lower()


def test_customer_cannot_add_address_to_other_customer():
    user1 = create_user(
        email="addowner1@test.com",
        full_name="Add Owner One",
        phone="9876543239",
    )

    customer1, token1 = create_customer(user1)

    user2 = create_user(
        email="addowner2@test.com",
        full_name="Add Owner Two",
        phone="9876543240",
    )

    _, token2 = create_customer(user2)

    response = client.post(
        f"/api/v1/customers/{customer1['id']}/addresses",
        headers=auth_headers(token2),
        json=address_payload(),
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data
    assert "own addresses" in data["detail"].lower()


def test_customer_cannot_update_other_customer_address():
    user1 = create_user(
        email="updateowner1@test.com",
        full_name="Update Owner One",
        phone="9876543241",
    )

    customer1, token1 = create_customer(user1)

    create_response = client.post(
        f"/api/v1/customers/{customer1['id']}/addresses",
        headers=auth_headers(token1),
        json=address_payload(),
    )

    assert create_response.status_code == 201

    address_id = create_response.json()["id"]

    user2 = create_user(
        email="updateowner2@test.com",
        full_name="Update Owner Two",
        phone="9876543242",
    )

    _, token2 = create_customer(user2)

    response = client.put(
        f"/api/v1/addresses/{address_id}",
        headers=auth_headers(token2),
        json={
            "city": "Bengaluru",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert "detail" in data
    assert "own addresses" in data["detail"].lower()


# ============================================================
# ADMIN ACCESS
# ============================================================

def test_admin_can_access_customer_addresses():
    user = create_user(
        email="admincustomer@test.com",
        full_name="Admin Customer",
        phone="9876543243",
    )

    customer, customer_token = create_customer(user)

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(customer_token),
        json=address_payload(),
    )

    assert response.status_code == 201

    admin = create_user(
        role=UserRole.ADMIN,
        email="addressadmin@test.com",
        full_name="Address Admin",
        phone="9876543244",
    )

    admin_token = login_user(
        admin["email"],
        admin["password"],
    )

    response = client.get(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1


# ============================================================
# VALIDATION
# ============================================================

def test_address_invalid_pincode():
    user = create_user(
        email="pincode@test.com",
        full_name="Pincode User",
        phone="9876543245",
    )

    customer, token = create_customer(user)

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(
            pincode="12345",
        ),
    )

    assert response.status_code == 422


def test_address_non_numeric_pincode():
    user = create_user(
        email="pincode2@test.com",
        full_name="Pincode User Two",
        phone="9876543246",
    )

    customer, token = create_customer(user)

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(
            pincode="ABC123",
        ),
    )

    assert response.status_code == 422


def test_invalid_address_type():
    user = create_user(
        email="addresstype@test.com",
        full_name="Address Type",
        phone="9876543247",
    )

    customer, token = create_customer(user)

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=address_payload(
            address_type="Office",
        ),
    )

    assert response.status_code == 422


def test_invalid_latitude():
    user = create_user(
        email="latitude@test.com",
        full_name="Latitude User",
        phone="9876543248",
    )

    customer, token = create_customer(user)

    payload = address_payload()
    payload["latitude"] = 100

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_longitude():
    user = create_user(
        email="longitude@test.com",
        full_name="Longitude User",
        phone="9876543249",
    )

    customer, token = create_customer(user)

    payload = address_payload()
    payload["longitude"] = 200

    response = client.post(
        f"/api/v1/customers/{customer['id']}/addresses",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# AUTHENTICATION
# ============================================================

def test_create_address_requires_authentication():
    response = client.post(
        "/api/v1/customers/1/addresses",
        json=address_payload(),
    )

    assert response.status_code == 401


def test_get_addresses_requires_authentication():
    response = client.get(
        "/api/v1/customers/1/addresses",
    )

    assert response.status_code == 401


def test_update_address_requires_authentication():
    response = client.put(
        "/api/v1/addresses/1",
        json={
            "city": "Hyderabad",
        },
    )

    assert response.status_code == 401