from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    id: int
    menu_item_id: int
    quantity: int
    unit_price: float
    item_total: float


class CartResponse(BaseModel):
    id: int
    customer_id: int
    items: list[CartItemResponse]
    subtotal: float