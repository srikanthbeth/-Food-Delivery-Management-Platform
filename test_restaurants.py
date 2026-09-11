import os
import time
import uuid

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from dependencies import get_db
from main import app


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


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ============================================================
# TEST DATABASE SETUP
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    Base.metadata.drop_all(bind=test_engine)


# ============================================================
# HELPERS
# ============================================================

def unique_email(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def register_user(
    full_name="Test User",
    role="Customer",
    email=None,
    password="Test@12345",
):
    if email is None:
        email = unique_email(role.lower().replace(" ", "_"))

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "phone": "9876543210",
            "password": password,
            "role": role,
        },
    )

    return response, email, password


def login_user(email, password):
    time.sleep(1.05)

    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def get_auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_logged_in_user(
    role,
    full_name=None,
    email=None,
    password="Test@12345",
):
    if full_name is None:
        full_name = f"{role} User"

    response, email, password = register_user(
        full_name=full_name,
        role=role,
        email=email,
        password=password,
    )

    assert response.status_code == 201

    user_id = response.json()["id"]

    login_response = login_user(
        email,
        password,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return (
        user_id,
        email,
        password,
        token,
    )


def restaurant_payload(owner_id, **overrides):
    payload = {
        "restaurant_name": "Spice Garden",
        "owner_id": owner_id,
        "address": "123 Banjara Hills Road",
        "city": "Hyderabad",
        "phone": "9876543210",
        "cuisine_type": "Indian",
        "opening_time": "10:00:00",
        "closing_time": "22:00:00",
        "status": "Open",
        "delivery_radius": 10,
    }

    payload.update(overrides)

    return payload


def create_restaurant(
    owner_id,
    token,
    **overrides,
):
    return client.post(
        "/api/v1/restaurants",
        headers=get_auth_header(token),
        json=restaurant_payload(
            owner_id,
            **overrides,
        ),
    )


# ============================================================
# RESTAURANT CREATION TESTS
# ============================================================

def test_admin_can_create_restaurant():

    owner_id, _, _, _ = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Restaurant Owner",
    )

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
        full_name="System Administrator",
    )

    response = create_restaurant(
        owner_id,
        admin_token,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_name"] == "Spice Garden"
    assert data["owner_id"] == owner_id
    assert data["city"] == "Hyderabad"
    assert data["cuisine_type"] == "Indian"
    assert data["status"] == "Open"
    assert data["delivery_radius"] == 10


def test_restaurant_owner_can_create_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Owner One",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        restaurant_name="Royal Biryani",
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_name"] == "Royal Biryani"
    assert data["owner_id"] == owner_id


def test_customer_cannot_create_restaurant():

    customer_id, _, _, customer_token = create_logged_in_user(
        role="Customer",
    )

    response = create_restaurant(
        customer_id,
        customer_token,
    )

    assert response.status_code == 403

    data = response.json()

    assert data["detail"] == "Insufficient permissions"


def test_restaurant_staff_cannot_create_restaurant():

    staff_id, _, _, staff_token = create_logged_in_user(
        role="Restaurant Staff",
    )

    response = create_restaurant(
        staff_id,
        staff_token,
    )

    assert response.status_code == 403


def test_delivery_partner_cannot_create_restaurant():

    delivery_id, _, _, delivery_token = create_logged_in_user(
        role="Delivery Partner",
    )

    response = create_restaurant(
        delivery_id,
        delivery_token,
    )

    assert response.status_code == 403


def test_restaurant_owner_cannot_create_for_another_owner():

    owner1_id, _, _, owner1_token = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Owner One",
    )

    owner2_id, _, _, _ = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Owner Two",
    )

    response = create_restaurant(
        owner2_id,
        owner1_token,
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "Restaurant owner can only create their own restaurant"
    )


def test_admin_cannot_create_with_invalid_owner():

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
        full_name="System Administrator",
    )

    response = create_restaurant(
        999999,
        admin_token,
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Restaurant owner not found"


def test_admin_cannot_create_for_customer():

    customer_id, _, _, _ = create_logged_in_user(
        role="Customer",
    )

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
        full_name="Admin User",
    )

    response = create_restaurant(
        customer_id,
        admin_token,
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "Restaurant owner must have Restaurant Owner role"
    )


# ============================================================
# RESTAURANT VALIDATION TESTS
# ============================================================

def test_restaurant_name_too_short():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        restaurant_name="A",
    )

    assert response.status_code == 422


def test_restaurant_name_missing():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    payload = restaurant_payload(owner_id)
    del payload["restaurant_name"]

    response = client.post(
        "/api/v1/restaurants",
        headers=get_auth_header(owner_token),
        json=payload,
    )

    assert response.status_code == 422


def test_restaurant_address_too_short():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        address="123",
    )

    assert response.status_code == 422


def test_restaurant_invalid_phone():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        phone="abcdefghij",
    )

    assert response.status_code == 422


def test_restaurant_invalid_delivery_radius():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        delivery_radius=0,
    )

    assert response.status_code == 422


def test_restaurant_negative_delivery_radius():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        delivery_radius=-5,
    )

    assert response.status_code == 422


def test_restaurant_invalid_status():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        status="Invalid Status",
    )

    assert response.status_code == 422


def test_restaurant_invalid_opening_closing_time():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        opening_time="22:00:00",
        closing_time="10:00:00",
    )

    assert response.status_code == 422


def test_restaurant_equal_opening_closing_time():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    response = create_restaurant(
        owner_id,
        owner_token,
        opening_time="10:00:00",
        closing_time="10:00:00",
    )

    assert response.status_code == 422


def test_restaurant_missing_owner_id():

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
    )

    payload = restaurant_payload(1)
    del payload["owner_id"]

    response = client.post(
        "/api/v1/restaurants",
        headers=get_auth_header(admin_token),
        json=payload,
    )

    assert response.status_code == 422


# ============================================================
# GET RESTAURANT TESTS
# ============================================================

def test_get_all_restaurants():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_restaurant(
        owner_id,
        owner_token,
        restaurant_name="Restaurant One",
    )

    response = client.get(
        "/api/v1/restaurants",
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_restaurant_by_id():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
        restaurant_name="Hyderabad Spice",
    )

    assert create_response.status_code == 201

    restaurant_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/restaurants/{restaurant_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == restaurant_id
    assert data["restaurant_name"] == "Hyderabad Spice"


def test_get_restaurant_not_found():

    response = client.get(
        "/api/v1/restaurants/999999",
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Restaurant not found"


# ============================================================
# RESTAURANT UPDATE TESTS
# ============================================================

def test_restaurant_owner_can_update_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner_token),
        json={
            "restaurant_name": "Updated Spice Garden",
            "city": "Bangalore",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == restaurant_id
    assert data["restaurant_name"] == "Updated Spice Garden"
    assert data["city"] == "Bangalore"


def test_admin_can_update_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
    )

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(admin_token),
        json={
            "status": "Busy",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Busy"


def test_owner_cannot_update_other_restaurant():

    owner1_id, _, _, owner1_token = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Owner One",
    )

    owner2_id, _, _, owner2_token = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Owner Two",
    )

    create_response = create_restaurant(
        owner2_id,
        owner2_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner1_token),
        json={
            "restaurant_name": "Unauthorized Update",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "You can only update your own restaurant"
    )


def test_customer_cannot_update_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    customer_id, _, _, customer_token = create_logged_in_user(
        role="Customer",
    )

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(customer_token),
        json={
            "restaurant_name": "Unauthorized Restaurant",
        },
    )

    assert response.status_code == 403


def test_staff_cannot_update_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    _, _, _, staff_token = create_logged_in_user(
        role="Restaurant Staff",
    )

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(staff_token),
        json={
            "restaurant_name": "Unauthorized Restaurant",
        },
    )

    assert response.status_code == 403


def test_update_restaurant_not_found():

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
    )

    response = client.put(
        "/api/v1/restaurants/999999",
        headers=get_auth_header(admin_token),
        json={
            "restaurant_name": "Updated Restaurant",
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Restaurant not found"


def test_update_restaurant_invalid_time():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner_token),
        json={
            "opening_time": "22:00:00",
            "closing_time": "10:00:00",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "Closing time must be after opening time"
    )


# ============================================================
# RESTAURANT DELETE TESTS
# ============================================================

def test_restaurant_owner_can_delete_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Restaurant deleted successfully"

    get_response = client.get(
        f"/api/v1/restaurants/{restaurant_id}",
    )

    assert get_response.status_code == 404


def test_admin_can_delete_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
    )

    response = client.delete(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True


def test_owner_cannot_delete_other_restaurant():

    owner1_id, _, _, owner1_token = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Owner One",
    )

    owner2_id, _, _, owner2_token = create_logged_in_user(
        role="Restaurant Owner",
        full_name="Owner Two",
    )

    create_response = create_restaurant(
        owner2_id,
        owner2_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner1_token),
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "You can only delete your own restaurant"
    )


def test_customer_cannot_delete_restaurant():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    _, _, _, customer_token = create_logged_in_user(
        role="Customer",
    )

    response = client.delete(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(customer_token),
    )

    assert response.status_code == 403


def test_delete_restaurant_not_found():

    _, _, _, admin_token = create_logged_in_user(
        role="Admin",
    )

    response = client.delete(
        "/api/v1/restaurants/999999",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Restaurant not found"


# ============================================================
# STATUS TESTS
# ============================================================

def test_restaurant_can_be_closed():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner_token),
        json={
            "status": "Closed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Closed"


def test_restaurant_can_be_busy():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner_token),
        json={
            "status": "Busy",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Busy"


def test_restaurant_can_be_temporarily_unavailable():

    owner_id, _, _, owner_token = create_logged_in_user(
        role="Restaurant Owner",
    )

    create_response = create_restaurant(
        owner_id,
        owner_token,
    )

    restaurant_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/restaurants/{restaurant_id}",
        headers=get_auth_header(owner_token),
        json={
            "status": "Temporarily Unavailable",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Temporarily Unavailable"