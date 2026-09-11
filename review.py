from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    order_id: int = Field(..., gt=0)

    restaurant_id: int | None = Field(
        default=None,
        gt=0,
    )

    food_item_id: int | None = Field(
        default=None,
        gt=0,
    )

    delivery_partner_id: int | None = Field(
        default=None,
        gt=0,
    )

    rating: int = Field(
        ...,
        ge=1,
        le=5,
    )

    review: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("review")
    @classmethod
    def validate_review(cls, value):
        if value is None:
            return value

        value = value.strip()

        if not value:
            return None

        return value


class ReviewResponse(BaseModel):
    id: int
    customer_id: int
    order_id: int
    restaurant_id: int | None
    food_item_id: int | None
    delivery_partner_id: int | None
    rating: int
    review: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )