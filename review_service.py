from sqlalchemy.orm import Session

from models.customer import Customer
from models.menu_item import MenuItem
from models.order import Order
from models.order_item import OrderItem
from models.restaurant import Restaurant
from models.review import Review
from models.user import User
from models.delivery_partner import DeliveryPartner

from repositories.review_repository import (
    create_review,
    get_customer_order_delivery_review,
    get_customer_order_food_review,
    get_customer_order_restaurant_review,
    get_food_item_reviews,
    get_restaurant_reviews,
)

from schemas.review import ReviewCreate

from utils.enums import (
    OrderStatus,
    UserRole,
)

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


def create_review_service(
    db: Session,
    data: ReviewCreate,
    current_user: User,
):
    # --------------------------------------------------------
    # CUSTOMER ONLY
    # --------------------------------------------------------

    if current_user.role != UserRole.CUSTOMER:
        raise PermissionError(
            "Only customers can create reviews"
        )

    # --------------------------------------------------------
    # GET CUSTOMER
    # --------------------------------------------------------

    customer = (
        db.query(Customer)
        .filter(
            Customer.user_id == current_user.id
        )
        .first()
    )

    if not customer:
        raise ResourceNotFoundException(
            "Customer profile not found"
        )

    # --------------------------------------------------------
    # GET ORDER
    # --------------------------------------------------------

    order = (
        db.query(Order)
        .filter(
            Order.id == data.order_id
        )
        .first()
    )

    if not order:
        raise ResourceNotFoundException(
            "Order not found"
        )

    # --------------------------------------------------------
    # CUSTOMER OWNERSHIP
    # --------------------------------------------------------

    if order.customer_id != customer.id:
        raise PermissionError(
            "You can only review your own orders"
        )

    # --------------------------------------------------------
    # DELIVERED ONLY
    # --------------------------------------------------------

    if order.order_status != OrderStatus.DELIVERED:
        raise BusinessRuleException(
            "Only delivered orders can be reviewed"
        )

    # --------------------------------------------------------
    # AT LEAST ONE TARGET
    # --------------------------------------------------------

    if not any(
        (
            data.restaurant_id,
            data.food_item_id,
            data.delivery_partner_id,
        )
    ):
        raise BusinessRuleException(
            "Review must target a restaurant, food item, or delivery partner"
        )

    # --------------------------------------------------------
    # RESTAURANT VALIDATION
    # --------------------------------------------------------

    if data.restaurant_id is not None:

        if data.restaurant_id != order.restaurant_id:
            raise BusinessRuleException(
                "Restaurant does not belong to this order"
            )

        restaurant = (
            db.query(Restaurant)
            .filter(
                Restaurant.id == data.restaurant_id
            )
            .first()
        )

        if not restaurant:
            raise ResourceNotFoundException(
                "Restaurant not found"
            )

        existing = get_customer_order_restaurant_review(
            db,
            customer.id,
            order.id,
            data.restaurant_id,
        )

        if existing:
            raise BusinessRuleException(
                "Restaurant review already exists for this order"
            )

    # --------------------------------------------------------
    # FOOD ITEM VALIDATION
    # --------------------------------------------------------

    if data.food_item_id is not None:

        order_item = (
            db.query(OrderItem)
            .filter(
                OrderItem.order_id == order.id,
                OrderItem.menu_item_id
                == data.food_item_id,
            )
            .first()
        )

        if not order_item:
            raise BusinessRuleException(
                "Food item does not belong to this order"
            )

        food_item = (
            db.query(MenuItem)
            .filter(
                MenuItem.id == data.food_item_id
            )
            .first()
        )

        if not food_item:
            raise ResourceNotFoundException(
                "Food item not found"
            )

        existing = get_customer_order_food_review(
            db,
            customer.id,
            order.id,
            data.food_item_id,
        )

        if existing:
            raise BusinessRuleException(
                "Food item review already exists for this order"
            )

    # --------------------------------------------------------
    # DELIVERY PARTNER VALIDATION
    # --------------------------------------------------------

    if data.delivery_partner_id is not None:

        if (
            order.delivery_partner_id
            != data.delivery_partner_id
        ):
            raise BusinessRuleException(
                "Delivery partner does not belong to this order"
            )

        delivery_partner = (
            db.query(DeliveryPartner)
            .filter(
                DeliveryPartner.id
                == data.delivery_partner_id
            )
            .first()
        )

        if not delivery_partner:
            raise ResourceNotFoundException(
                "Delivery partner not found"
            )

        existing = get_customer_order_delivery_review(
            db,
            customer.id,
            order.id,
            data.delivery_partner_id,
        )

        if existing:
            raise BusinessRuleException(
                "Delivery partner review already exists for this order"
            )

    # --------------------------------------------------------
    # CREATE REVIEW
    # --------------------------------------------------------

    review = Review(
        customer_id=customer.id,
        order_id=order.id,
        restaurant_id=data.restaurant_id,
        food_item_id=data.food_item_id,
        delivery_partner_id=data.delivery_partner_id,
        rating=data.rating,
        review=data.review,
    )

    return create_review(
        db,
        review,
    )


def get_restaurant_reviews_service(
    db: Session,
    restaurant_id: int,
):
    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id
        )
        .first()
    )

    if not restaurant:
        raise ResourceNotFoundException(
            "Restaurant not found"
        )

    return get_restaurant_reviews(
        db,
        restaurant_id,
    )


def get_food_item_reviews_service(
    db: Session,
    food_item_id: int,
):
    food_item = (
        db.query(MenuItem)
        .filter(
            MenuItem.id == food_item_id
        )
        .first()
    )

    if not food_item:
        raise ResourceNotFoundException(
            "Food item not found"
        )

    return get_food_item_reviews(
        db,
        food_item_id,
    )