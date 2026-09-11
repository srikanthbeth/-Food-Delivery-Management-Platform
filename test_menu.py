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

# Import ALL models so Base.metadata knows about every table
from models.user import User
from models.restaurant import Restaurant
from models.menu_item import MenuItem


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
    autoflush=False,
    autocommit=False,
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
# DATABASE SETUP / TEARDOWN
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    Base.metadata.drop_all(bind=test_engine)


# ============================================================
# HELPERS
# ============================================================

def unique_email(prefix: str = "user") -> str:
    return (
        f"{prefix}_{uuid.uuid4().hex[:8]}"
        "@example.com"
    )


def register_user(
    full_name="Test User",
    role="Customer",
    email=None,
    password="Test@12345",
):
    if email is None:
        email = unique_email("user")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": role,
        },
    )

    return response, email, password


def login_user(
    email: str,
    password: str,
):
    time.sleep(1.05)

    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def get_auth_header(access_token: str):
    return {
        "Authorization": f"Bearer {access_token}"
    }


def create_user_and_login(
    full_name="Test User",
    role="Customer",
):
    response, email, password = register_user(
        full_name=full_name,
        role=role,
    )

    assert response.status_code == 201

    login_response = login_user(
        email,
        password,
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return response.json(), token


def create_restaurant(
    token: str,
    owner_id: int,
    restaurant_name="Test Restaurant",
):
    response = client.post(
        "/api/v1/restaurants",
        headers=get_auth_header(token),
        json={
            "restaurant_name": restaurant_name,
            "owner_id": owner_id,
            "address": "123 Main Street",
            "city": "Hyderabad",
            "phone": "9876543210",
            "cuisine_type": "Indian",
            "opening_time": "09:00:00",
            "closing_time": "22:00:00",
            "status": "Open",
            "delivery_radius": 10,
        },
    )

    return response


def create_menu_item(
    token: str,
    restaurant_id: int,
    name="Chicken Biryani",
    price=280,
    category="Main Course",
    availability=True,
    vegetarian=False,
    spicy_level=3,
    preparation_time=30,
):
    return client.post(
        "/api/v1/menu/items",
        headers=get_auth_header(token),
        json={
            "restaurant_id": restaurant_id,
            "category": category,
            "name": name,
            "description": "Delicious food item",
            "price": price,
            "preparation_time": preparation_time,
            "availability": availability,
            "vegetarian": vegetarian,
            "spicy_level": spicy_level,
        },
    )


def setup_restaurant_owner():
    user, token = create_user_and_login(
        full_name="Restaurant Owner",
        role="Restaurant Owner",
    )

    restaurant_response = create_restaurant(
        token=token,
        owner_id=user["id"],
    )

    assert restaurant_response.status_code == 201

    return user, token, restaurant_response.json()


def setup_admin():
    user, token = create_user_and_login(
        full_name="System Administrator",
        role="Admin",
    )

    return user, token


def setup_staff(restaurant_id: int):
    user, token = create_user_and_login(
        full_name="Restaurant Staff",
        role="Restaurant Staff",
    )

    db = TestingSessionLocal()

    try:
        staff = (
            db.query(User)
            .filter(User.id == user["id"])
            .first()
        )

        staff.restaurant_id = restaurant_id

        db.commit()
        db.refresh(staff)

    finally:
        db.close()

    return user, token


# ============================================================
# CREATE MENU ITEM TESTS
# ============================================================

def test_create_menu_item_as_admin():

    admin, admin_token = setup_admin()

    owner_response, owner_email, owner_password = register_user(
        full_name="Restaurant Owner",
        role="Restaurant Owner",
    )

    assert owner_response.status_code == 201

    owner_id = owner_response.json()["id"]

    restaurant_response = create_restaurant(
        token=admin_token,
        owner_id=owner_id,
    )

    assert restaurant_response.status_code == 201

    restaurant_id = restaurant_response.json()["id"]

    response = create_menu_item(
        token=admin_token,
        restaurant_id=restaurant_id,
        name="Chicken Biryani",
        price=280,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == restaurant_id
    assert data["name"] == "Chicken Biryani"
    assert data["price"] == 280
    assert data["category"] == "Main Course"
    assert data["preparation_time"] == 30
    assert data["availability"] is True
    assert data["vegetarian"] is False
    assert data["spicy_level"] == 3


def test_create_menu_item_as_owner():

    owner, owner_token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=owner_token,
        restaurant_id=restaurant["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["restaurant_id"] == restaurant["id"]
    assert data["name"] == "Chicken Biryani"


def test_create_menu_item_as_assigned_staff():

    owner, owner_token, restaurant = setup_restaurant_owner()

    staff, staff_token = setup_staff(
        restaurant["id"]
    )

    response = create_menu_item(
        token=staff_token,
        restaurant_id=restaurant["id"],
    )

    assert response.status_code == 201


def test_customer_cannot_create_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    customer, customer_token = create_user_and_login(
        full_name="Customer",
        role="Customer",
    )

    response = create_menu_item(
        token=customer_token,
        restaurant_id=restaurant["id"],
    )

    assert response.status_code == 403


def test_delivery_partner_cannot_create_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    driver, driver_token = create_user_and_login(
        full_name="Delivery Partner",
        role="Delivery Partner",
    )

    response = create_menu_item(
        token=driver_token,
        restaurant_id=restaurant["id"],
    )

    assert response.status_code == 403


def test_unassigned_staff_cannot_create_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    staff, staff_token = create_user_and_login(
        full_name="Unassigned Staff",
        role="Restaurant Staff",
    )

    response = create_menu_item(
        token=staff_token,
        restaurant_id=restaurant["id"],
    )

    assert response.status_code == 403


def test_staff_cannot_create_menu_item_for_other_restaurant():

    owner1, token1, restaurant1 = setup_restaurant_owner()

    owner2, token2, restaurant2 = setup_restaurant_owner()

    staff, staff_token = setup_staff(
        restaurant1["id"]
    )

    response = create_menu_item(
        token=staff_token,
        restaurant_id=restaurant2["id"],
    )

    assert response.status_code == 400


def test_owner_cannot_create_menu_item_for_other_restaurant():

    owner1, token1, restaurant1 = setup_restaurant_owner()

    owner2, token2, restaurant2 = setup_restaurant_owner()

    response = create_menu_item(
        token=token1,
        restaurant_id=restaurant2["id"],
    )

    assert response.status_code == 400


def test_create_menu_item_invalid_restaurant():

    admin, admin_token = setup_admin()

    response = create_menu_item(
        token=admin_token,
        restaurant_id=999999,
    )

    assert response.status_code == 404


# ============================================================
# CREATE MENU ITEM VALIDATION
# ============================================================

def test_menu_item_price_zero_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        price=0,
    )

    assert response.status_code == 422


def test_menu_item_negative_price_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        price=-100,
    )

    assert response.status_code == 422


def test_menu_item_preparation_time_zero_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        preparation_time=0,
    )

    assert response.status_code == 422


def test_menu_item_negative_preparation_time_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        preparation_time=-10,
    )

    assert response.status_code == 422


def test_menu_item_negative_spicy_level_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        spicy_level=-1,
    )

    assert response.status_code == 422


def test_menu_item_spicy_level_above_five_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        spicy_level=6,
    )

    assert response.status_code == 422


def test_menu_item_empty_name_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        name="",
    )

    assert response.status_code == 422


def test_menu_item_empty_category_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        category="",
    )

    assert response.status_code == 422


def test_menu_item_missing_price():

    owner, token, restaurant = setup_restaurant_owner()

    response = client.post(
        "/api/v1/menu/items",
        headers=get_auth_header(token),
        json={
            "restaurant_id": restaurant["id"],
            "category": "Main Course",
            "name": "Biryani",
            "preparation_time": 30,
            "availability": True,
            "vegetarian": False,
            "spicy_level": 3,
        },
    )

    assert response.status_code == 422


def test_menu_item_missing_preparation_time():

    owner, token, restaurant = setup_restaurant_owner()

    response = client.post(
        "/api/v1/menu/items",
        headers=get_auth_header(token),
        json={
            "restaurant_id": restaurant["id"],
            "category": "Main Course",
            "name": "Biryani",
            "price": 250,
            "availability": True,
            "vegetarian": False,
            "spicy_level": 3,
        },
    )

    assert response.status_code == 422


# ============================================================
# GET MENU ITEMS
# ============================================================

def test_get_all_menu_items():

    owner, token, restaurant = setup_restaurant_owner()

    create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        name="Chicken Biryani",
    )

    create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        name="Paneer Biryani",
        vegetarian=True,
    )

    response = client.get(
        "/api/v1/menu/items"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    # This test file contains data created by
    # previous tests, so only verify that the
    # two newly-created items are present.
    names = {
        item["name"]
        for item in data
    }

    assert "Chicken Biryani" in names
    assert "Paneer Biryani" in names


def test_get_menu_items_by_restaurant():

    owner, token, restaurant = setup_restaurant_owner()

    create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    response = client.get(
        f"/api/v1/menu/items?restaurant_id={restaurant['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["restaurant_id"] == restaurant["id"]


def test_get_menu_items_invalid_restaurant():

    response = client.get(
        "/api/v1/menu/items?restaurant_id=999999"
    )

    assert response.status_code == 404


def test_get_menu_item_by_id():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/menu/items/{item_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == item_id
    assert data["name"] == "Chicken Biryani"


def test_get_menu_item_not_found():

    response = client.get(
        "/api/v1/menu/items/999999"
    )

    assert response.status_code == 404


# ============================================================
# UPDATE MENU ITEM
# ============================================================

def test_owner_can_update_menu_item():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token),
        json={
            "name": "Special Chicken Biryani",
            "price": 300,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Special Chicken Biryani"
    assert data["price"] == 300


def test_admin_can_update_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    admin, admin_token = setup_admin()

    create_response = create_menu_item(
        token=owner_token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(admin_token),
        json={
            "price": 350,
        },
    )

    assert response.status_code == 200

    assert response.json()["price"] == 350


def test_assigned_staff_can_update_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    staff, staff_token = setup_staff(
        restaurant["id"]
    )

    create_response = create_menu_item(
        token=owner_token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(staff_token),
        json={
            "price": 275,
        },
    )

    assert response.status_code == 200

    assert response.json()["price"] == 275


def test_staff_cannot_update_other_restaurant_item():

    owner1, token1, restaurant1 = setup_restaurant_owner()

    owner2, token2, restaurant2 = setup_restaurant_owner()

    staff, staff_token = setup_staff(
        restaurant1["id"]
    )

    create_response = create_menu_item(
        token=token2,
        restaurant_id=restaurant2["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(staff_token),
        json={
            "price": 500,
        },
    )

    assert response.status_code == 400


def test_owner_cannot_update_other_restaurant_item():

    owner1, token1, restaurant1 = setup_restaurant_owner()

    owner2, token2, restaurant2 = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token2,
        restaurant_id=restaurant2["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token1),
        json={
            "price": 500,
        },
    )

    assert response.status_code == 400


def test_customer_cannot_update_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    customer, customer_token = create_user_and_login(
        full_name="Customer",
        role="Customer",
    )

    create_response = create_menu_item(
        token=owner_token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(customer_token),
        json={
            "price": 500,
        },
    )

    assert response.status_code == 403


def test_update_menu_item_not_found():

    admin, admin_token = setup_admin()

    response = client.put(
        "/api/v1/menu/items/999999",
        headers=get_auth_header(admin_token),
        json={
            "price": 500,
        },
    )

    assert response.status_code == 404


# ============================================================
# UPDATE VALIDATION
# ============================================================

def test_update_price_zero_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token),
        json={
            "price": 0,
        },
    )

    assert response.status_code == 422


def test_update_negative_price_invalid():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token),
        json={
            "price": -50,
        },
    )

    assert response.status_code == 422


def test_update_invalid_preparation_time():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token),
        json={
            "preparation_time": 0,
        },
    )

    assert response.status_code == 422


def test_update_invalid_spicy_level():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token),
        json={
            "spicy_level": 6,
        },
    )

    assert response.status_code == 422


# ============================================================
# DELETE MENU ITEM
# ============================================================

def test_owner_can_delete_menu_item():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token),
    )

    assert response.status_code == 200

    assert response.json()["success"] is True


def test_admin_can_delete_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    admin, admin_token = setup_admin()

    create_response = create_menu_item(
        token=owner_token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 200


def test_assigned_staff_can_delete_menu_item():

    owner, owner_token, restaurant = setup_restaurant_owner()

    staff, staff_token = setup_staff(
        restaurant["id"]
    )

    create_response = create_menu_item(
        token=owner_token,
        restaurant_id=restaurant["id"],
    )

    item_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(staff_token),
    )

    assert response.status_code == 200


def test_staff_cannot_delete_other_restaurant_item():

    owner1, token1, restaurant1 = setup_restaurant_owner()

    owner2, token2, restaurant2 = setup_restaurant_owner()

    staff, staff_token = setup_staff(
        restaurant1["id"]
    )

    create_response = create_menu_item(
        token=token2,
        restaurant_id=restaurant2["id"],
    )

    item_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(staff_token),
    )

    assert response.status_code == 400


def test_owner_cannot_delete_other_restaurant_item():

    owner1, token1, restaurant1 = setup_restaurant_owner()

    owner2, token2, restaurant2 = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token2,
        restaurant_id=restaurant2["id"],
    )

    item_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token1),
    )

    assert response.status_code == 400


def test_delete_menu_item_not_found():

    admin, admin_token = setup_admin()

    response = client.delete(
        "/api/v1/menu/items/999999",
        headers=get_auth_header(admin_token),
    )

    assert response.status_code == 404


# ============================================================
# AVAILABILITY TESTS
# ============================================================

def test_menu_item_unavailable():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        availability=False,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["availability"] is False


def test_menu_item_available():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        availability=True,
    )

    assert response.status_code == 201

    assert response.json()["availability"] is True


def test_update_menu_item_availability():

    owner, token, restaurant = setup_restaurant_owner()

    create_response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        availability=True,
    )

    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/menu/items/{item_id}",
        headers=get_auth_header(token),
        json={
            "availability": False,
        },
    )

    assert response.status_code == 200

    assert response.json()["availability"] is False


# ============================================================
# VEGETARIAN / SPICY LEVEL TESTS
# ============================================================

def test_vegetarian_menu_item():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        name="Paneer Tikka",
        vegetarian=True,
        spicy_level=2,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["vegetarian"] is True
    assert data["spicy_level"] == 2


def test_non_vegetarian_menu_item():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        vegetarian=False,
    )

    assert response.status_code == 201

    assert response.json()["vegetarian"] is False


def test_spicy_level_zero_valid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        spicy_level=0,
    )

    assert response.status_code == 201

    assert response.json()["spicy_level"] == 0


def test_spicy_level_five_valid():

    owner, token, restaurant = setup_restaurant_owner()

    response = create_menu_item(
        token=token,
        restaurant_id=restaurant["id"],
        spicy_level=5,
    )

    assert response.status_code == 201

    assert response.json()["spicy_level"] == 5


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

def test_create_menu_item_without_token():

    response = client.post(
        "/api/v1/menu/items",
        json={
            "restaurant_id": 1,
            "category": "Main Course",
            "name": "Biryani",
            "description": "Test",
            "price": 250,
            "preparation_time": 30,
            "availability": True,
            "vegetarian": False,
            "spicy_level": 2,
        },
    )

    assert response.status_code in [401, 403]


def test_update_menu_item_without_token():

    response = client.put(
        "/api/v1/menu/items/1",
        json={
            "price": 300,
        },
    )

    assert response.status_code in [401, 403]


def test_delete_menu_item_without_token():

    response = client.delete(
        "/api/v1/menu/items/1"
    )

    assert response.status_code in [401, 403]