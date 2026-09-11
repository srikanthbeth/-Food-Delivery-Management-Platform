from sqlalchemy.orm import Session

from models.review import Review


def create_review(
    db: Session,
    review: Review,
) -> Review:
    db.add(review)
    db.commit()
    db.refresh(review)

    return review


def get_review_by_id(
    db: Session,
    review_id: int,
):
    return (
        db.query(Review)
        .filter(Review.id == review_id)
        .first()
    )


def get_restaurant_reviews(
    db: Session,
    restaurant_id: int,
):
    return (
        db.query(Review)
        .filter(
            Review.restaurant_id == restaurant_id
        )
        .order_by(
            Review.created_at.desc()
        )
        .all()
    )


def get_food_item_reviews(
    db: Session,
    food_item_id: int,
):
    return (
        db.query(Review)
        .filter(
            Review.food_item_id == food_item_id
        )
        .order_by(
            Review.created_at.desc()
        )
        .all()
    )


def get_customer_order_restaurant_review(
    db: Session,
    customer_id: int,
    order_id: int,
    restaurant_id: int,
):
    return (
        db.query(Review)
        .filter(
            Review.customer_id == customer_id,
            Review.order_id == order_id,
            Review.restaurant_id == restaurant_id,
        )
        .first()
    )


def get_customer_order_food_review(
    db: Session,
    customer_id: int,
    order_id: int,
    food_item_id: int,
):
    return (
        db.query(Review)
        .filter(
            Review.customer_id == customer_id,
            Review.order_id == order_id,
            Review.food_item_id == food_item_id,
        )
        .first()
    )


def get_customer_order_delivery_review(
    db: Session,
    customer_id: int,
    order_id: int,
    delivery_partner_id: int,
):
    return (
        db.query(Review)
        .filter(
            Review.customer_id == customer_id,
            Review.order_id == order_id,
            Review.delivery_partner_id == delivery_partner_id,
        )
        .first()
    )