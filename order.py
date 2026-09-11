
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from utils.enums import OrderStatus, PaymentStatus


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey(
            "restaurants.id",
        ),
        nullable=False,
        index=True,
    )

    address_id: Mapped[int] = mapped_column(
        ForeignKey(
            "addresses.id",
        ),
        nullable=False,
        index=True,
    )

    # ========================================================
    # DELIVERY PARTNER
    # ========================================================

    delivery_partner_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "delivery_partners.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================
    # ORDER AMOUNTS
    # ========================================================

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    delivery_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    discount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    tax: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    # ========================================================
    # ORDER STATUS
    # ========================================================

    order_status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(
            OrderStatus,
            name="order_status",
        ),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(
            PaymentStatus,
            name="payment_status",
        ),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

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

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    customer = relationship(
        "Customer",
        foreign_keys=[customer_id],
    )

    restaurant = relationship(
        "Restaurant",
        foreign_keys=[restaurant_id],
    )

    address = relationship(
        "Address",
        foreign_keys=[address_id],
    )

    delivery_partner = relationship(
        "DeliveryPartner",
        back_populates="orders",
        foreign_keys=[delivery_partner_id],
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    tracking_history = relationship(
    "OrderTracking",
    back_populates="order",
    cascade="all, delete-orphan",
    order_by="OrderTracking.timestamp",
)

    payment = relationship(
    "Payment",
    back_populates="order",
    uselist=False,
    cascade="all, delete-orphan",
)

    refunds = relationship(
    "Refund",
    back_populates="order",
    cascade="all, delete-orphan",
)

