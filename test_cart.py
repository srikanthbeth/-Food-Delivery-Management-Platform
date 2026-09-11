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
from models.restaurant import Restaurant
from models.menu_item import MenuItem
from models.customer import Customer
from models.cart import Cart
from models.cart_item import CartItem
from utils.enums import UserRole, RestaurantStatus
from utils.security import hash_password, create_access_token


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
# TEST DATABASE SETUP
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def teardown_module():
    Base.metadata.remove if hasattr(Base.metadata, "remove") else None


# ============================================================
# HELPERS
# ============================================================

def create_user(
    role=UserRole.CUSTOMER,
    email=None,
    full_name="Test User",
    phone="9876543210",
    password="Password123",
):
    if email is None:
        email = f"user_{uuid4().hex[:8]}@test.com"

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

    user_data = {
        "id": user.id,
        "email": email,
        "password": password,
        "phone": phone,
    }

    db.close()

    return user_data


def get_auth_headers(user_id, role):
    token = create_access_token(
        user_id=user_id,
        role=role.value,
    )

    return {
        "Authorization": f"Bearer {token}"
    }


def create_customer(user=None):
    if user is None:
        user = create_user()

    db = TestingSessionLocal()

    customer = Customer(
        user_id=user["id"],
        name="Test Customer",
        email=f"customer_{uuid4().hex[:8]}@test.com",
        phone=user["phone"],
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    customer_id = customer.id

    db.close()

    return customer_id


def create_restaurant(
    owner_id,
    restaurant_name=None,
):
    if restaurant_name is None:
        restaurant_name = (
            f"Restaurant {uuid4().hex[:8]}"
        )

    db = TestingSessionLocal()

    restaurant = Restaurant(
        restaurant_name=restaurant_name,
        owner_id=owner_id,
        address="123 Main Street",
        city="Hyderabad",
        phone="9876543210",
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

    return restaurant_id


def create_menu_item(
    restaurant_id,
    name=None,
    price=250,
    availability=True,
):
    if name is None:
        name = f"Food {uuid4().hex[:8]}"

    db = TestingSessionLocal()

    item = MenuItem(
        restaurant_id=restaurant_id,
        category="Main Course",
        name=name,
        description="Test food item",
        price=price,
        preparation_time=20,
        availability=availability,
        vegetarian=True,
        spicy_level=2,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    item_id = item.id

    db.close()

    return item_id


def get_cart_from_db(customer_id):
    db = TestingSessionLocal()

    cart = (
        db.query(Cart)
        .filter(Cart.customer_id == customer_id)
        .first()
    )

    db.close()

    return cart


# ============================================================
# ADD TO CART
# ============================================================

def test_add_item_to_cart():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(owner["id"])
    menu_item_id = create_menu_item(
        restaurant_id,
        price=250,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 2,
        },
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer_id
    assert len(data["items"]) == 1
    assert data["items"][0]["menu_item_id"] == menu_item_id
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["unit_price"] == 250
    assert data["items"][0]["item_total"] == 500
    assert data["subtotal"] == 500


def test_add_same_item_increases_quantity():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(owner["id"])
    menu_item_id = create_menu_item(
        restaurant_id,
        price=100,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response1 = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 2,
        },
        headers=headers,
    )

    assert response1.status_code == 201

    response2 = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 3,
        },
        headers=headers,
    )

    assert response2.status_code == 201

    data = response2.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5
    assert data["subtotal"] == 500


def test_add_multiple_items_same_restaurant():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(owner["id"])

    item1 = create_menu_item(
        restaurant_id,
        price=100,
    )

    item2 = create_menu_item(
        restaurant_id,
        price=200,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response1 = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item1,
            "quantity": 2,
        },
        headers=headers,
    )

    assert response1.status_code == 201

    response2 = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item2,
            "quantity": 1,
        },
        headers=headers,
    )

    assert response2.status_code == 201

    data = response2.json()

    assert len(data["items"]) == 2
    assert data["subtotal"] == 400


# ============================================================
# ONE RESTAURANT PER CART
# ============================================================

def test_cart_cannot_contain_items_from_different_restaurants():
    user = create_user()
    customer_id = create_customer(user)

    owner1 = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    owner2 = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant1 = create_restaurant(
        owner1["id"]
    )

    restaurant2 = create_restaurant(
        owner2["id"]
    )

    item1 = create_menu_item(
        restaurant1,
        price=150,
    )

    item2 = create_menu_item(
        restaurant2,
        price=200,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response1 = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item1,
            "quantity": 1,
        },
        headers=headers,
    )

    assert response1.status_code == 201

    response2 = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item2,
            "quantity": 1,
        },
        headers=headers,
    )

    assert response2.status_code == 400
    assert (
        "only one restaurant"
        in response2.json()["detail"].lower()
    )


# ============================================================
# UNAVAILABLE ITEMS
# ============================================================

def test_unavailable_menu_item_cannot_be_added():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id,
        availability=False,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 1,
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert (
        "unavailable"
        in response.json()["detail"].lower()
    )


# ============================================================
# INVALID MENU ITEM
# ============================================================

def test_add_nonexistent_menu_item():
    user = create_user()
    customer_id = create_customer(user)

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": 999999,
            "quantity": 1,
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Menu item not found"
    )


# ============================================================
# QUANTITY VALIDATION
# ============================================================

def test_zero_quantity_rejected():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 0,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_negative_quantity_rejected():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": -1,
        },
        headers=headers,
    )

    assert response.status_code == 422


# ============================================================
# GET CART
# ============================================================

def test_get_cart():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id,
        price=300,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    add_response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 2,
        },
        headers=headers,
    )

    assert add_response.status_code == 201

    response = client.get(
        f"/api/v1/cart?customer_id={customer_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == customer_id
    assert len(data["items"]) == 1
    assert data["subtotal"] == 600


def test_get_empty_cart():
    user = create_user()
    customer_id = create_customer(user)

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.get(
        f"/api/v1/cart?customer_id={customer_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["items"] == []
    assert data["subtotal"] == 0


# ============================================================
# SUBTOTAL
# ============================================================

def test_cart_subtotal_calculation():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    item1 = create_menu_item(
        restaurant_id,
        price=100,
    )

    item2 = create_menu_item(
        restaurant_id,
        price=250,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item1,
            "quantity": 2,
        },
        headers=headers,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item2,
            "quantity": 3,
        },
        headers=headers,
    )

    assert response.status_code == 201

    data = response.json()

    # 100*2 + 250*3 = 950
    assert data["subtotal"] == 950


# ============================================================
# UPDATE CART ITEM
# ============================================================

def test_update_cart_item():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id,
        price=200,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    add_response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 2,
        },
        headers=headers,
    )

    assert add_response.status_code == 201

    item_id = add_response.json()["items"][0]["id"]

    response = client.put(
        f"/api/v1/cart/items/{item_id}",
        json={
            "quantity": 5,
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["quantity"] == 5
    assert data["subtotal"] == 1000


def test_update_cart_item_zero_quantity_rejected():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    add_response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 1,
        },
        headers=headers,
    )

    item_id = add_response.json()["items"][0]["id"]

    response = client.put(
        f"/api/v1/cart/items/{item_id}",
        json={
            "quantity": 0,
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_update_nonexistent_cart_item():
    user = create_user()

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.put(
        "/api/v1/cart/items/999999",
        json={
            "quantity": 2,
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Cart item not found"
    )


# ============================================================
# REMOVE ITEM
# ============================================================

def test_remove_cart_item():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    add_response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 2,
        },
        headers=headers,
    )

    item_id = add_response.json()["items"][0]["id"]

    response = client.delete(
        f"/api/v1/cart/items/{item_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["subtotal"] == 0


def test_remove_nonexistent_cart_item():
    user = create_user()

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.delete(
        "/api/v1/cart/items/999999",
        headers=headers,
    )

    assert response.status_code == 404


# ============================================================
# CLEAR CART
# ============================================================

def test_clear_cart():
    user = create_user()
    customer_id = create_customer(user)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    item1 = create_menu_item(
        restaurant_id,
        price=100,
    )

    item2 = create_menu_item(
        restaurant_id,
        price=200,
    )

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item1,
            "quantity": 2,
        },
        headers=headers,
    )

    client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": item2,
            "quantity": 1,
        },
        headers=headers,
    )

    response = client.delete(
        f"/api/v1/cart/clear?customer_id={customer_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["subtotal"] == 0


# ============================================================
# CUSTOMER ACCESS CONTROL
# ============================================================

def test_customer_cannot_access_other_customer_cart():
    user1 = create_user()
    customer1 = create_customer(user1)

    user2 = create_user()
    customer2 = create_customer(user2)

    headers = get_auth_headers(
        user1["id"],
        UserRole.CUSTOMER,
    )

    response = client.get(
        f"/api/v1/cart?customer_id={customer2}",
        headers=headers,
    )

    assert response.status_code == 400
    assert (
        "own cart"
        in response.json()["detail"].lower()
    )


def test_customer_cannot_add_to_other_customer_cart():
    user1 = create_user()
    create_customer(user1)

    user2 = create_user()
    customer2 = create_customer(user2)

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id
    )

    headers = get_auth_headers(
        user1["id"],
        UserRole.CUSTOMER,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer2}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 1,
        },
        headers=headers,
    )

    assert response.status_code == 400


# ============================================================
# ADMIN ACCESS
# ============================================================

def test_admin_can_access_customer_cart():
    customer_user = create_user()
    customer_id = create_customer(
        customer_user
    )

    admin = create_user(
        role=UserRole.ADMIN
    )

    headers = get_auth_headers(
        admin["id"],
        UserRole.ADMIN,
    )

    response = client.get(
        f"/api/v1/cart?customer_id={customer_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == customer_id


def test_admin_can_add_to_customer_cart():
    customer_user = create_user()
    customer_id = create_customer(
        customer_user
    )

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    restaurant_id = create_restaurant(
        owner["id"]
    )

    menu_item_id = create_menu_item(
        restaurant_id,
        price=300,
    )

    admin = create_user(
        role=UserRole.ADMIN
    )

    headers = get_auth_headers(
        admin["id"],
        UserRole.ADMIN,
    )

    response = client.post(
        f"/api/v1/cart/items?customer_id={customer_id}",
        json={
            "menu_item_id": menu_item_id,
            "quantity": 1,
        },
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["subtotal"] == 300


# ============================================================
# ROLE RESTRICTIONS
# ============================================================

def test_delivery_partner_cannot_access_cart():
    customer_user = create_user()
    customer_id = create_customer(
        customer_user
    )

    delivery_partner = create_user(
        role=UserRole.DELIVERY_PARTNER
    )

    headers = get_auth_headers(
        delivery_partner["id"],
        UserRole.DELIVERY_PARTNER,
    )

    response = client.get(
        f"/api/v1/cart?customer_id={customer_id}",
        headers=headers,
    )

    assert response.status_code == 403


def test_restaurant_owner_cannot_access_cart():
    customer_user = create_user()
    customer_id = create_customer(
        customer_user
    )

    owner = create_user(
        role=UserRole.RESTAURANT_OWNER
    )

    headers = get_auth_headers(
        owner["id"],
        UserRole.RESTAURANT_OWNER,
    )

    response = client.get(
        f"/api/v1/cart?customer_id={customer_id}",
        headers=headers,
    )

    assert response.status_code == 403


# ============================================================
# CUSTOMER NOT FOUND
# ============================================================

def test_cart_customer_not_found():
    user = create_user()

    headers = get_auth_headers(
        user["id"],
        UserRole.CUSTOMER,
    )

    response = client.get(
        "/api/v1/cart?customer_id=999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Customer not found"
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def test_add_cart_item_requires_authentication():
    response = client.post(
        "/api/v1/cart/items?customer_id=1",
        json={
            "menu_item_id": 1,
            "quantity": 1,
        },
    )

    assert response.status_code == 401


def test_get_cart_requires_authentication():
    response = client.get(
        "/api/v1/cart?customer_id=1"
    )

    assert response.status_code == 401


def test_update_cart_item_requires_authentication():
    response = client.put(
        "/api/v1/cart/items/1",
        json={
            "quantity": 2,
        },
    )

    assert response.status_code == 401


def test_remove_cart_item_requires_authentication():
    response = client.delete(
        "/api/v1/cart/items/1"
    )

    assert response.status_code == 401


def test_clear_cart_requires_authentication():
    response = client.delete(
        "/api/v1/cart/clear?customer_id=1"
    )

    assert response.status_code == 401