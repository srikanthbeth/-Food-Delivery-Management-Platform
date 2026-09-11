from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from utils.enums import OrderStatus, PaymentStatus


class OrderCreate(BaseModel):
    address_id: int = Field(
        ...,
        gt=0,
    )

    coupon_code: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    unit_price: Decimal
    item_total: Decimal

    model_config = ConfigDict(
        from_attributes=True
    )


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    address_id: int

    subtotal: Decimal
    delivery_fee: Decimal
    discount: Decimal
    tax: Decimal
    total_amount: Decimal

    order_status: OrderStatus
    payment_status: PaymentStatus

    created_at: datetime
    updated_at: datetime

    items: list[OrderItemResponse]

    model_config = ConfigDict(
        from_attributes=True
    )


class OrderCancelResponse(BaseModel):
    success: bool
    message: str
    order_id: int
    order_status: OrderStatus

from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from utils.enums import OrderStatus, PaymentStatus


class OrderCreate(BaseModel):
    address_id: int = Field(
        ...,
        gt=0,
    )

    coupon_code: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    unit_price: Decimal
    item_total: Decimal

    model_config = ConfigDict(
        from_attributes=True
    )


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    restaurant_id: int
    address_id: int

    subtotal: Decimal
    delivery_fee: Decimal
    discount: Decimal
    tax: Decimal
    total_amount: Decimal

    order_status: OrderStatus
    payment_status: PaymentStatus

    created_at: datetime
    updated_at: datetime

    items: list[OrderItemResponse]

    model_config = ConfigDict(
        from_attributes=True
    )


class OrderCancelResponse(BaseModel):
    success: bool
    message: str
    order_id: int
    order_status: OrderStatus


class OrderSearchResult(BaseModel):
    items: list[OrderResponse]
    page: int
    limit: int
    total: int
    pages: int   