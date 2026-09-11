from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from utils.enums import DeliveryAvailabilityStatus


class DeliveryPartnerCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    phone: str = Field(
        ...,
        min_length=10,
        max_length=15,
    )

    vehicle_type: str = Field(
        ...,
        min_length=2,
        max_length=50,
    )

    vehicle_number: str = Field(
        ...,
        min_length=2,
        max_length=30,
    )

    current_location: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator(
        "name",
        "vehicle_type",
        "vehicle_number",
    )
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Field cannot be empty"
            )

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()

        if not value.isdigit():
            raise ValueError(
                "Phone must contain only digits"
            )

        if len(value) < 10 or len(value) > 15:
            raise ValueError(
                "Phone must be between 10 and 15 digits"
            )

        return value


class DeliveryPartnerResponse(BaseModel):
    id: int
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    availability_status: DeliveryAvailabilityStatus
    current_location: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


class DeliveryPartnerStatusUpdate(BaseModel):
    availability_status: DeliveryAvailabilityStatus


class AssignDriverResponse(BaseModel):
    success: bool
    message: str
    order_id: int
    delivery_partner_id: int
    order_status: str
    driver_status: DeliveryAvailabilityStatus