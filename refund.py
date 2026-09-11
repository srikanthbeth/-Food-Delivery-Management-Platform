from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.enums import PaymentTransactionStatus


class RefundCreate(BaseModel):

    amount: Decimal = Field(
        ...,
        gt=0,
    )

    reason: str = Field(
        ...,
        min_length=3,
        max_length=500,
    )

    refund_transaction_id: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Refund reason cannot be empty"
            )

        return value

    @field_validator("refund_transaction_id")
    @classmethod
    def validate_transaction_id(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Refund transaction ID cannot be empty"
            )

        return value


class RefundResponse(BaseModel):

    id: int
    payment_id: int
    order_id: int
    amount: Decimal
    reason: str
    refund_transaction_id: str
    refund_status: PaymentTransactionStatus
    refunded_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )