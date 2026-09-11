from sqlalchemy.orm import Session

from models.delivery_partner import DeliveryPartner
from models.order import Order
from models.user import User
from repositories.delivery_repository import (
    create_delivery_partner,
    get_all_delivery_partners,
    get_delivery_partner_by_id,
    get_delivery_partner_by_phone,
    get_delivery_partner_by_vehicle_number,
    update_delivery_partner,
)
from schemas.delivery import DeliveryPartnerCreate
from utils.enums import (
    DeliveryAvailabilityStatus,
    OrderStatus,
    UserRole,
)
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


# ============================================================
# ACTIVE ORDER STATUSES
# ============================================================

ACTIVE_ORDER_STATUSES = (
    OrderStatus.PENDING,
    OrderStatus.ACCEPTED,
    OrderStatus.PREPARING,
    OrderStatus.READY,
    OrderStatus.PICKED_UP,
    OrderStatus.OUT_FOR_DELIVERY,
)


# ============================================================
# CREATE DELIVERY PARTNER
# ============================================================

def create_delivery_partner_service(
    db: Session,
    data: DeliveryPartnerCreate,
    current_user: User,
):

    if current_user.role != UserRole.ADMIN:
        raise PermissionError(
            "Only admin can create delivery partners"
        )

    existing_phone = get_delivery_partner_by_phone(
        db,
        data.phone,
    )

    if existing_phone:
        raise BusinessRuleException(
            "Delivery partner phone already exists"
        )

    existing_vehicle = get_delivery_partner_by_vehicle_number(
        db,
        data.vehicle_number,
    )

    if existing_vehicle:
        raise BusinessRuleException(
            "Vehicle number already exists"
        )

    delivery_partner = DeliveryPartner(
        name=data.name,
        phone=data.phone,
        vehicle_type=data.vehicle_type,
        vehicle_number=data.vehicle_number,
        availability_status=(
            DeliveryAvailabilityStatus.AVAILABLE
        ),
        current_location=data.current_location,
    )

    return create_delivery_partner(
        db,
        delivery_partner,
    )


# ============================================================
# GET DELIVERY PARTNERS
# ============================================================

def get_delivery_partners_service(
    db: Session,
    current_user: User,
):

    allowed_roles = (
        UserRole.ADMIN,
        UserRole.RESTAURANT_OWNER,
        UserRole.RESTAURANT_STAFF,
    )

    if current_user.role not in allowed_roles:
        raise PermissionError(
            "You do not have permission to view delivery partners"
        )

    return get_all_delivery_partners(db)


# ============================================================
# UPDATE DELIVERY PARTNER STATUS
# ============================================================

def update_delivery_partner_status_service(
    db: Session,
    delivery_partner_id: int,
    status: DeliveryAvailabilityStatus,
    current_user: User,
):

    if current_user.role != UserRole.ADMIN:
        raise PermissionError(
            "Only admin can update delivery partner status"
        )

    delivery_partner = get_delivery_partner_by_id(
        db,
        delivery_partner_id,
    )

    if not delivery_partner:
        raise ResourceNotFoundException(
            "Delivery partner not found"
        )

    # --------------------------------------------------------
    # Driver cannot manually become AVAILABLE while
    # having an active order.
    # --------------------------------------------------------

    if status == DeliveryAvailabilityStatus.AVAILABLE:

        active_order = (
            db.query(Order)
            .filter(
                Order.delivery_partner_id
                == delivery_partner_id,
                Order.order_status.in_(
                    ACTIVE_ORDER_STATUSES
                ),
            )
            .first()
        )

        if active_order:
            raise BusinessRuleException(
                "Delivery partner has an active delivery"
            )

    delivery_partner = update_delivery_partner(
        db,
        delivery_partner,
        availability_status=status,
    )

    return delivery_partner


# ============================================================
# ASSIGN DRIVER
# ============================================================

def assign_driver_service(
    db: Session,
    order_id: int,
    delivery_partner_id: int,
    current_user: User,
):

    allowed_roles = (
        UserRole.ADMIN,
        UserRole.RESTAURANT_OWNER,
        UserRole.RESTAURANT_STAFF,
    )

    if current_user.role not in allowed_roles:
        raise PermissionError(
            "You do not have permission to assign delivery partners"
        )

    # --------------------------------------------------------
    # Get order
    # --------------------------------------------------------

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise ResourceNotFoundException(
            "Order not found"
        )

    # --------------------------------------------------------
    # Delivered / Cancelled orders cannot be assigned
    # --------------------------------------------------------

    if order.order_status == OrderStatus.DELIVERED:

        raise BusinessRuleException(
            "Delivered order cannot be assigned to a driver"
        )

    if order.order_status == OrderStatus.CANCELLED:

        raise BusinessRuleException(
            "Cancelled order cannot be assigned to a driver"
        )

    # --------------------------------------------------------
    # Order cannot have two drivers
    # --------------------------------------------------------

    if order.delivery_partner_id is not None:

        raise BusinessRuleException(
            "Order already has a delivery partner"
        )

    # --------------------------------------------------------
    # Get driver
    # --------------------------------------------------------

    delivery_partner = get_delivery_partner_by_id(
        db,
        delivery_partner_id,
    )

    if not delivery_partner:

        raise ResourceNotFoundException(
            "Delivery partner not found"
        )

    # --------------------------------------------------------
    # Driver must be available
    # --------------------------------------------------------

    if (
        delivery_partner.availability_status
        != DeliveryAvailabilityStatus.AVAILABLE
    ):

        raise BusinessRuleException(
            "Delivery partner is not available"
        )

    # --------------------------------------------------------
    # Driver cannot have another active order
    # --------------------------------------------------------

    active_order = (
        db.query(Order)
        .filter(
            Order.delivery_partner_id
            == delivery_partner_id,
            Order.order_status.in_(
                ACTIVE_ORDER_STATUSES
            ),
        )
        .first()
    )

    if active_order:

        raise BusinessRuleException(
            "Delivery partner already has an active delivery"
        )

    # --------------------------------------------------------
    # Assign driver
    # --------------------------------------------------------

    order.delivery_partner_id = delivery_partner_id

    delivery_partner.availability_status = (
        DeliveryAvailabilityStatus.ON_DELIVERY
    )

    db.commit()

    db.refresh(order)
    db.refresh(delivery_partner)

    return {
        "success": True,
        "message": "Delivery partner assigned successfully",
        "order_id": order.id,
        "delivery_partner_id": delivery_partner.id,
        "order_status": order.order_status.value,
        "driver_status": (
            delivery_partner.availability_status
        ),
    }