from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user

from models.user import User

from schemas.review import (
    ReviewCreate,
    ReviewResponse,
)

from services.review_service import (
    create_review_service,
    get_food_item_reviews_service,
    get_restaurant_reviews_service,
)

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


router = APIRouter(
    tags=["Reviews & Ratings"],
)


@router.post(
    "/reviews",
    response_model=ReviewResponse,
    status_code=201,
)
def create_review(
    data: ReviewCreate,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    try:
        return create_review_service(
            db,
            data,
            current_user,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    except BusinessRuleException as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/restaurants/{restaurant_id}/reviews",
    response_model=list[ReviewResponse],
)
def get_restaurant_reviews(
    restaurant_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_restaurant_reviews_service(
            db,
            restaurant_id,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.get(
    "/food-items/{food_item_id}/reviews",
    response_model=list[ReviewResponse],
)
def get_food_item_reviews(
    food_item_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_food_item_reviews_service(
            db,
            food_item_id,
        )

    except ResourceNotFoundException as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )