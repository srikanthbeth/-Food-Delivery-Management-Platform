from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.enums import PaymentMethod, PaymentTransactionStatus


class PaymentCreate(BaseModel):

    amount: Decimal = Field(
        ...,
        gt=0,
    )

    payment_method: PaymentMethod

    transaction_id: str = Field(
        ...,
        min_length=3,
        max_length=100,
    )

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "Transaction ID cannot be empty"
            )

        return value


class PaymentResponse(BaseModel):

    id: int
    order_id: int
    amount: Decimal
    payment_method: PaymentMethod
    transaction_id: str
    payment_status: PaymentTransactionStatus
    paid_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )