
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    customer_id: int = Field(..., gt=0)
    order_id: int | None = Field(default=None, gt=0)

    notification_type: str = Field(
        ...,
        min_length=3,
        max_length=50,
    )

    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
    )

    message: str = Field(
        ...,
        min_length=3,
        max_length=2000,
    )


class NotificationResponse(BaseModel):
    id: int
    customer_id: int
    order_id: int | None

    notification_type: str
    title: str
    message: str

    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationReadResponse(BaseModel):
    success: bool
    message: str
    notification_id: int
    is_read: bool

