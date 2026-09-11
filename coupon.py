from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


VALID_DISCOUNT_TYPES = {
    "Percentage",
    "Fixed",
}


class CouponCreate(BaseModel):
    coupon_code: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    discount_type: str

    discount_value: Decimal = Field(
        ...,
        gt=0,
    )

    minimum_order_value: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )

    maximum_discount: Decimal | None = Field(
        default=None,
        gt=0,
    )

    start_date: date

    expiry_date: date

    usage_limit: int | None = Field(
        default=None,
        gt=0,
    )

    status: bool = True

    @field_validator("coupon_code")
    @classmethod
    def validate_coupon_code(
        cls,
        value: str,
    ) -> str:

        value = value.strip().upper()

        if not value:
            raise ValueError(
                "Coupon code cannot be empty"
            )

        return value

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(
        cls,
        value: str,
    ) -> str:

        value = value.strip().title()

        if value not in VALID_DISCOUNT_TYPES:
            raise ValueError(
                "Discount type must be Percentage or Fixed"
            )

        return value

    @model_validator(mode="after")
    def validate_coupon_dates(self):

        if self.expiry_date < self.start_date:
            raise ValueError(
                "Expiry date must be greater than or equal to start date"
            )

        if (
            self.discount_type == "Percentage"
            and self.discount_value > 100
        ):
            raise ValueError(
                "Percentage discount cannot exceed 100"
            )

        if (
            self.discount_type == "Fixed"
            and self.maximum_discount is not None
        ):
            raise ValueError(
                "Maximum discount is only applicable to Percentage coupons"
            )

        return self


class CouponResponse(BaseModel):
    id: int
    coupon_code: str
    discount_type: str
    discount_value: Decimal
    minimum_order_value: Decimal
    maximum_discount: Decimal | None
    start_date: date
    expiry_date: date
    usage_limit: int | None
    usage_count: int
    status: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class CouponApplyRequest(BaseModel):
    coupon_code: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    order_amount: Decimal = Field(
        ...,
        gt=0,
    )

    @field_validator("coupon_code")
    @classmethod
    def validate_coupon_code(
        cls,
        value: str,
    ) -> str:

        return value.strip().upper()


class CouponApplyResponse(BaseModel):
    coupon_code: str
    order_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal
    message: str