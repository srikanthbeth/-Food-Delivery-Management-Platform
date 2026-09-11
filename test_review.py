
import os
from datetime import time
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "restaurant_food_delivery_test"
)

from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
from main import app

from models.customer import Customer
from models.delivery_partner import DeliveryPartner
from models.menu_item import MenuItem
from models.order import Order
from models.order_item import OrderItem
from models.restaurant import Restaurant
from models.user import User

from utils.enums import (
    DeliveryAvailabilityStatus,
    OrderStatus,
    PaymentStatus,
    RestaurantStatus,
    UserRole,
)

from utils.security import hash_password


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

def unique_email(prefix="review"):
    safe_prefix = "".join(
        ch.lower() if ch.isalnum() else "_"
        for ch in prefix
    ).strip("_")

    return f"{safe_prefix}_{uuid4().hex[:10]}@example.com"


def create_user_and_login(
    role=UserRole.CUSTOMER,
):
    db = SessionLocal()

    email = unique_email(role.value)
    phone = f"9{uuid4().int % 10**9:09d}"

    user = User(
        full_name=f"Review Test {role.value}",
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
            name="Review Test Customer",
            email=email,
            phone=phone,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        customer_id = customer.id

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


def create_restaurant():
    db = SessionLocal()

    owner = User(
        full_name="Review Restaurant Owner",
        email=unique_email("restaurant_owner"),
        phone=f"8{uuid4().int % 10**9:09d}",
        password_hash=hash_password("Test@123"),
        role=UserRole.RESTAURANT_OWNER,
        is_active=True,
    )

    db.add(owner)
    db.commit()
    db.refresh(owner)

    restaurant = Restaurant(
        restaurant_name=f"Review Restaurant {uuid4().hex[:6]}",
        owner_id=owner.id,
        address="123 Review Street",
        city="Hyderabad",
        phone=f"7{uuid4().int % 10**9:09d}",
        cuisine_type="Indian",
        opening_time=time(9, 0),
        closing_time=time(23, 0),
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
):
    db = SessionLocal()

    if name is None:
        name = f"Review Food {uuid4().hex[:6]}"

    menu_item = MenuItem(
        restaurant_id=restaurant_id,
        category="Main Course",
        name=name,
        price=Decimal("150.00"),
        preparation_time=20,
        availability=True,
        vegetarian=True,
        spicy_level=1,
    )

    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)

    menu_item_id = menu_item.id

    db.close()

    return menu_item_id


def create_delivery_partner():
    db = SessionLocal()

    partner = DeliveryPartner(
        name="Review Delivery Partner",
        phone=f"6{uuid4().int % 10**9:09d}",
        vehicle_type="Bike",
        vehicle_number=f"TS{uuid4().int % 10**6:06d}",
        availability_status=DeliveryAvailabilityStatus.AVAILABLE,
        current_location="Hyderabad",
    )

    db.add(partner)
    db.commit()
    db.refresh(partner)

    partner_id = partner.id

    db.close()

    return partner_id


def create_order(
    customer_id,
    restaurant_id,
    menu_item_id=None,
    delivery_partner_id=None,
    order_status=OrderStatus.DELIVERED,
):
    db = SessionLocal()

    # --------------------------------------------------------
    # Verify customer
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
    # Create address
    # --------------------------------------------------------

    from models.address import Address

    address = Address(
        customer_id=customer_id,
        address_line="123 Review Address",
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
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        address_id=address.id,
        delivery_partner_id=delivery_partner_id,
        subtotal=Decimal("150.00"),
        delivery_fee=Decimal("40.00"),
        discount=Decimal("0.00"),
        tax=Decimal("7.50"),
        total_amount=Decimal("197.50"),
        order_status=order_status,
        payment_status=PaymentStatus.PAID,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # --------------------------------------------------------
    # Create order item
    # --------------------------------------------------------

    if menu_item_id is not None:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item_id,
            quantity=1,
            unit_price=Decimal("150.00"),
            item_total=Decimal("150.00"),
        )

        db.add(order_item)
        db.commit()

    order_id = order.id

    db.close()

    return order_id


def review_payload(
    order_id,
    restaurant_id=None,
    food_item_id=None,
    delivery_partner_id=None,
    rating=5,
    review="Excellent experience",
):
    return {
        "order_id": order_id,
        "restaurant_id": restaurant_id,
        "food_item_id": food_item_id,
        "delivery_partner_id": delivery_partner_id,
        "rating": rating,
        "review": review,
    }


# ============================================================
# RESTAURANT REVIEWS
# ============================================================

def test_create_restaurant_review():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=5,
            review="Excellent restaurant",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["order_id"] == order_id
    assert data["restaurant_id"] == restaurant_id
    assert data["rating"] == 5
    assert data["review"] == "Excellent restaurant"


def test_get_restaurant_reviews():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=4,
            review="Good restaurant",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    response = client.get(
        f"/api/v1/restaurants/{restaurant_id}/reviews"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) >= 1
    assert data[-1]["restaurant_id"] == restaurant_id


def test_restaurant_not_found():
    response = client.get(
        "/api/v1/restaurants/999999/reviews"
    )

    assert response.status_code == 404


# ============================================================
# FOOD ITEM REVIEWS
# ============================================================

def test_create_food_item_review():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    menu_item_id = create_menu_item(
        restaurant_id
    )

    order_id = create_order(
        customer_id,
        restaurant_id,
        menu_item_id=menu_item_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            food_item_id=menu_item_id,
            rating=5,
            review="Very tasty food",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["food_item_id"] == menu_item_id
    assert data["rating"] == 5


def test_get_food_item_reviews():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    menu_item_id = create_menu_item(
        restaurant_id
    )

    order_id = create_order(
        customer_id,
        restaurant_id,
        menu_item_id=menu_item_id,
    )

    client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            food_item_id=menu_item_id,
            rating=4,
            review="Good food",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    response = client.get(
        f"/api/v1/food-items/{menu_item_id}/reviews"
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data) >= 1
    assert data[-1]["food_item_id"] == menu_item_id


def test_food_item_not_found():
    response = client.get(
        "/api/v1/food-items/999999/reviews"
    )

    assert response.status_code == 404


# ============================================================
# DELIVERY PARTNER REVIEWS
# ============================================================

def test_create_delivery_partner_review():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    delivery_partner_id = create_delivery_partner()

    order_id = create_order(
        customer_id,
        restaurant_id,
        delivery_partner_id=delivery_partner_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            delivery_partner_id=delivery_partner_id,
            rating=5,
            review="Excellent delivery",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert (
        data["delivery_partner_id"]
        == delivery_partner_id
    )

    assert data["rating"] == 5


# ============================================================
# MULTIPLE REVIEW TYPES
# ============================================================

def test_customer_can_review_restaurant_and_food_item():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    menu_item_id = create_menu_item(
        restaurant_id
    )

    order_id = create_order(
        customer_id,
        restaurant_id,
        menu_item_id=menu_item_id,
    )

    restaurant_response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=5,
            review="Great restaurant",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert restaurant_response.status_code == 201, (
        restaurant_response.text
    )

    food_response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            food_item_id=menu_item_id,
            rating=4,
            review="Tasty food",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert food_response.status_code == 201, (
        food_response.text
    )


# ============================================================
# DELIVERED ORDER RULE
# ============================================================

def test_pending_order_cannot_be_reviewed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
        order_status=OrderStatus.PENDING,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "delivered" in response.text.lower()


def test_accepted_order_cannot_be_reviewed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
        order_status=OrderStatus.ACCEPTED,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400


def test_cancelled_order_cannot_be_reviewed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
        order_status=OrderStatus.CANCELLED,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400


# ============================================================
# OWNERSHIP
# ============================================================

def test_customer_cannot_review_another_customer_order():
    customer1_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    _, token2, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer1_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {token2}"
        },
    )

    assert response.status_code == 403
    assert "own orders" in response.text.lower()


# ============================================================
# AUTHENTICATION / AUTHORIZATION
# ============================================================

def test_create_review_requires_authentication():
    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
    )

    assert response.status_code in (401, 403)


def test_non_customer_cannot_create_review():
    _, token, _ = create_user_and_login(
        UserRole.RESTAURANT_OWNER
    )

    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


# ============================================================
# RATING VALIDATION
# ============================================================

def test_rating_cannot_be_zero():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=0,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_rating_cannot_be_negative():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=-1,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_rating_cannot_exceed_five():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=6,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_rating_five_is_valid():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=5,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text


def test_rating_one_is_valid():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            rating=1,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text


# ============================================================
# TARGET VALIDATION
# ============================================================

def test_review_requires_target():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            rating=5,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400


def test_restaurant_must_belong_to_order():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant1_id = create_restaurant()
    restaurant2_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant1_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant2_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "restaurant" in response.text.lower()


def test_food_item_must_belong_to_order():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    item1_id = create_menu_item(
        restaurant_id
    )

    item2_id = create_menu_item(
        restaurant_id
    )

    order_id = create_order(
        customer_id,
        restaurant_id,
        menu_item_id=item1_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            food_item_id=item2_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "food item" in response.text.lower()


def test_delivery_partner_must_belong_to_order():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    partner1_id = create_delivery_partner()
    partner2_id = create_delivery_partner()

    order_id = create_order(
        customer_id,
        restaurant_id,
        delivery_partner_id=partner1_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            delivery_partner_id=partner2_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "delivery partner" in response.text.lower()


# ============================================================
# DUPLICATE REVIEWS
# ============================================================

def test_duplicate_restaurant_review_not_allowed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    payload = review_payload(
        order_id,
        restaurant_id=restaurant_id,
        rating=5,
    )

    first = client.post(
        "/api/v1/reviews",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert first.status_code == 201, first.text

    second = client.post(
        "/api/v1/reviews",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert second.status_code == 400
    assert "already exists" in second.text.lower()


def test_duplicate_food_item_review_not_allowed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    menu_item_id = create_menu_item(
        restaurant_id
    )

    order_id = create_order(
        customer_id,
        restaurant_id,
        menu_item_id=menu_item_id,
    )

    payload = review_payload(
        order_id,
        food_item_id=menu_item_id,
        rating=5,
    )

    first = client.post(
        "/api/v1/reviews",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert first.status_code == 201, first.text

    second = client.post(
        "/api/v1/reviews",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert second.status_code == 400
    assert "already exists" in second.text.lower()


def test_duplicate_delivery_partner_review_not_allowed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    partner_id = create_delivery_partner()

    order_id = create_order(
        customer_id,
        restaurant_id,
        delivery_partner_id=partner_id,
    )

    payload = review_payload(
        order_id,
        delivery_partner_id=partner_id,
        rating=5,
    )

    first = client.post(
        "/api/v1/reviews",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert first.status_code == 201, first.text

    second = client.post(
        "/api/v1/reviews",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert second.status_code == 400
    assert "already exists" in second.text.lower()


# ============================================================
# ORDER NOT FOUND
# ============================================================

def test_review_order_not_found():
    _, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            999999,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


# ============================================================
# REVIEW TEXT VALIDATION
# ============================================================

def test_review_text_is_trimmed():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            review="   Excellent restaurant   ",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["review"] == (
        "Excellent restaurant"
    )


def test_empty_review_text_becomes_none():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            review="   ",
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["review"] is None


def test_review_text_cannot_exceed_maximum_length():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
            review="x" * 1001,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


# ============================================================
# REVIEW RESPONSE
# ============================================================

def test_review_response_contains_created_at():
    customer_id, token, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert "id" in data
    assert "created_at" in data
    assert data["customer_id"] == customer_id
    assert data["order_id"] == order_id


# ============================================================
# ADMIN
# ============================================================

def test_admin_cannot_create_review():
    _, admin_token, _ = create_user_and_login(
        UserRole.ADMIN
    )

    customer_id, _, _ = create_user_and_login(
        UserRole.CUSTOMER
    )

    restaurant_id = create_restaurant()

    order_id = create_order(
        customer_id,
        restaurant_id,
    )

    response = client.post(
        "/api/v1/reviews",
        json=review_payload(
            order_id,
            restaurant_id=restaurant_id,
        ),
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 403

