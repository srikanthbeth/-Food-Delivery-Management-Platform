from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MenuItemCreate(BaseModel):
    restaurant_id: int = Field(
        ...,
        gt=0,
    )

    category: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
    )

    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    preparation_time: int = Field(
        ...,
        gt=0,
    )

    availability: bool = True

    vegetarian: bool = False

    spicy_level: int = Field(
        0,
        ge=0,
        le=5,
    )

    @field_validator("category", "name")
    @classmethod
    def validate_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value


class MenuItemUpdate(BaseModel):
    category: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
    )

    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=150,
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
    )

    price: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    preparation_time: Optional[int] = Field(
        None,
        gt=0,
    )

    availability: Optional[bool] = None

    vegetarian: Optional[bool] = None

    spicy_level: Optional[int] = Field(
        None,
        ge=0,
        le=5,
    )

    @field_validator("category", "name")
    @classmethod
    def validate_text(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError("Field cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value

from pydantic import BaseModel, ConfigDict

class MenuItemResponse(BaseModel):
    id: int
    restaurant_id: int
    category: str
    name: str
    description: str | None
    price: float
    preparation_time: int
    availability: bool
    vegetarian: bool
    spicy_level: int

    model_config = ConfigDict(from_attributes=True)


from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MenuItemCreate(BaseModel):
    restaurant_id: int = Field(
        ...,
        gt=0,
    )

    category: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
    )

    price: Decimal = Field(
        ...,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    preparation_time: int = Field(
        ...,
        gt=0,
    )

    availability: bool = True

    vegetarian: bool = False

    spicy_level: int = Field(
        0,
        ge=0,
        le=5,
    )

    @field_validator("category", "name")
    @classmethod
    def validate_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value


class MenuItemUpdate(BaseModel):
    category: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
    )

    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=150,
    )

    description: Optional[str] = Field(
        None,
        max_length=1000,
    )

    price: Optional[Decimal] = Field(
        None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )

    preparation_time: Optional[int] = Field(
        None,
        gt=0,
    )

    availability: Optional[bool] = None

    vegetarian: Optional[bool] = None

    spicy_level: Optional[int] = Field(
        None,
        ge=0,
        le=5,
    )

    @field_validator("category", "name")
    @classmethod
    def validate_text(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                raise ValueError("Field cannot be empty")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                return None

        return value


class MenuItemResponse(BaseModel):
    id: int
    restaurant_id: int
    category: str
    name: str
    description: str | None
    price: float
    preparation_time: int
    availability: bool
    vegetarian: bool
    spicy_level: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# FOOD SEARCH
# ============================================================

class MenuItemSearchResult(BaseModel):
    items: list[MenuItemResponse]
    page: int
    limit: int
    total: int
    pages: int   