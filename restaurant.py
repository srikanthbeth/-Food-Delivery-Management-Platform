from datetime import time
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from utils.enums import RestaurantStatus


class RestaurantCreate(BaseModel):
    restaurant_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    owner_id: int = Field(
        ...,
        gt=0,
    )

    address: str = Field(
        ...,
        min_length=5,
        max_length=255,
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
    )

    cuisine_type: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    opening_time: time
    closing_time: time

    status: RestaurantStatus = RestaurantStatus.OPEN

    delivery_radius: int = Field(
        ...,
        gt=0,
    )

    @field_validator("restaurant_name", "city", "cuisine_type")
    @classmethod
    def validate_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str):
        value = value.strip()

        if not value.isdigit():
            raise ValueError("Phone must contain only digits")

        return value

    @field_validator("closing_time")
    @classmethod
    def validate_times(cls, closing_time, info):
        opening_time = info.data.get("opening_time")

        if opening_time and closing_time <= opening_time:
            raise ValueError(
                "Closing time must be after opening time"
            )

        return closing_time


class RestaurantUpdate(BaseModel):
    restaurant_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=150,
    )

    address: Optional[str] = Field(
        None,
        min_length=5,
        max_length=255,
    )

    city: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
    )

    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
    )

    cuisine_type: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
    )

    opening_time: Optional[time] = None
    closing_time: Optional[time] = None

    status: Optional[RestaurantStatus] = None

    delivery_radius: Optional[int] = Field(
        None,
        gt=0,
    )


class RestaurantResponse(BaseModel):
    id: int
    restaurant_name: str
    owner_id: int
    address: str
    city: str
    phone: str
    cuisine_type: str
    opening_time: time
    closing_time: time
    status: RestaurantStatus
    delivery_radius: int

    class Config:
        from_attributes = True

from datetime import time
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from utils.enums import RestaurantStatus


class RestaurantCreate(BaseModel):
    restaurant_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    owner_id: int = Field(
        ...,
        gt=0,
    )

    address: str = Field(
        ...,
        min_length=5,
        max_length=255,
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
    )

    cuisine_type: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    opening_time: time
    closing_time: time

    status: RestaurantStatus = RestaurantStatus.OPEN

    delivery_radius: int = Field(
        ...,
        gt=0,
    )

    @field_validator("restaurant_name", "city", "cuisine_type")
    @classmethod
    def validate_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str):
        value = value.strip()

        if not value.isdigit():
            raise ValueError("Phone must contain only digits")

        return value

    @field_validator("closing_time")
    @classmethod
    def validate_times(cls, closing_time, info):
        opening_time = info.data.get("opening_time")

        if opening_time and closing_time <= opening_time:
            raise ValueError(
                "Closing time must be after opening time"
            )

        return closing_time


class RestaurantUpdate(BaseModel):
    restaurant_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=150,
    )

    address: Optional[str] = Field(
        None,
        min_length=5,
        max_length=255,
    )

    city: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
    )

    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=20,
    )

    cuisine_type: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
    )

    opening_time: Optional[time] = None
    closing_time: Optional[time] = None

    status: Optional[RestaurantStatus] = None

    delivery_radius: Optional[int] = Field(
        None,
        gt=0,
    )


class RestaurantResponse(BaseModel):
    id: int
    restaurant_name: str
    owner_id: int
    address: str
    city: str
    phone: str
    cuisine_type: str
    opening_time: time
    closing_time: time
    status: RestaurantStatus
    delivery_radius: int

    class Config:
        from_attributes = True


# ============================================================
# RESTAURANT SEARCH
# ============================================================

class RestaurantSearchResponse(BaseModel):
    id: int
    restaurant_name: str
    owner_id: int
    address: str
    city: str
    phone: str
    cuisine_type: str
    opening_time: time
    closing_time: time
    status: RestaurantStatus
    delivery_radius: int

    rating: float
    delivery_time: float


class RestaurantSearchResult(BaseModel):
    items: list[RestaurantSearchResponse]
    page: int
    limit: int
    total: int
    pages: int        