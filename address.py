from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_ADDRESS_TYPES = {
    "Home",
    "Work",
    "Other",
}


class AddressCreate(BaseModel):
    address_line: str = Field(
        ...,
        min_length=5,
        max_length=255,
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    pincode: str = Field(
        ...,
        min_length=6,
        max_length=6,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    address_type: str = Field(
        default="Other",
    )

    is_default: bool = False

    @field_validator("address_line", "city")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: str) -> str:
        value = value.strip()

        if not value.isdigit():
            raise ValueError("Pincode must contain only digits")

        if len(value) != 6:
            raise ValueError("Pincode must contain exactly 6 digits")

        return value

    @field_validator("address_type")
    @classmethod
    def validate_address_type(cls, value: str) -> str:
        value = value.strip()

        if value not in VALID_ADDRESS_TYPES:
            raise ValueError(
                "Address type must be Home, Work, or Other"
            )

        return value


class AddressUpdate(BaseModel):
    address_line: str | None = Field(
        default=None,
        min_length=5,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    pincode: str | None = Field(
        default=None,
        min_length=6,
        max_length=6,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    address_type: str | None = None

    is_default: bool | None = None

    @field_validator("address_line", "city")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty")

        return value

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value.isdigit():
            raise ValueError("Pincode must contain only digits")

        if len(value) != 6:
            raise ValueError("Pincode must contain exactly 6 digits")

        return value

    @field_validator("address_type")
    @classmethod
    def validate_address_type(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if value not in VALID_ADDRESS_TYPES:
            raise ValueError(
                "Address type must be Home, Work, or Other"
            )

        return value


class AddressResponse(BaseModel):
    id: int
    customer_id: int
    address_line: str
    city: str
    pincode: str
    latitude: float | None
    longitude: float | None
    address_type: str
    is_default: bool

    model_config = ConfigDict(
        from_attributes=True,
    )