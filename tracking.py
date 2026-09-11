from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from utils.enums import TrackingStatus


# ============================================================
# CREATE TRACKING
# ============================================================

class TrackingCreate(BaseModel):

    status: TrackingStatus

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    remarks: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator("location", "remarks")
    @classmethod
    def validate_optional_text(
        cls,
        value: str | None,
    ):

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value


# ============================================================
# TRACKING RESPONSE
# ============================================================

class TrackingResponse(BaseModel):

    id: int
    order_id: int
    status: TrackingStatus
    location: str | None
    remarks: str | None
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True
    )