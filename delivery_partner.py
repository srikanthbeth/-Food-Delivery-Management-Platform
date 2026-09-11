from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from utils.enums import DeliveryAvailabilityStatus


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    vehicle_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )

    availability_status: Mapped[
        DeliveryAvailabilityStatus
    ] = mapped_column(
        SQLEnum(
            DeliveryAvailabilityStatus,
            name="delivery_availability_status",
        ),
        nullable=False,
        default=DeliveryAvailabilityStatus.AVAILABLE,
        index=True,
    )

    current_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    orders = relationship(
        "Order",
        back_populates="delivery_partner",
    )