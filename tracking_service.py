from sqlalchemy.orm import Session

from models.order import Order
from models.order_tracking import OrderTracking
from models.user import User
from models.customer import Customer

from repositories.tracking_repository import (
    create_tracking,
    get_tracking_by_order,
)
from schemas.tracking import TrackingCreate
from utils.enums import OrderStatus, UserRole
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


# ============================================================
# CREATE ORDER TRACKING
# ============================================================

def create_tracking_service(
    db: Session,
    order_id: int,
    data: TrackingCreate,
    current_user: User,
):
    # --------------------------------------------------------
    # ROLE CHECK
    # --------------------------------------------------------

    allowed_roles = (
        UserRole.ADMIN,
        UserRole.RESTAURANT_OWNER,
        UserRole.RESTAURANT_STAFF,
        UserRole.DELIVERY_PARTNER,
    )

    if current_user.role not in allowed_roles:
        raise PermissionError(
            "You do not have permission to create order tracking"
        )

    # --------------------------------------------------------
    # GET ORDER
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
    # DELIVERED / CANCELLED ORDERS
    # --------------------------------------------------------

    if order.order_status == OrderStatus.DELIVERED:
        raise BusinessRuleException(
            "Delivered order cannot receive tracking"
        )

    if order.order_status == OrderStatus.CANCELLED:
        raise BusinessRuleException(
            "Cancelled order cannot receive tracking"
        )

    # --------------------------------------------------------
    # CREATE TRACKING RECORD
    # --------------------------------------------------------

    tracking = OrderTracking(
        order_id=order_id,
        status=data.status,
        location=data.location,
        remarks=data.remarks,
    )

    tracking = create_tracking(
        db,
        tracking,
    )

    # --------------------------------------------------------
    # SYNCHRONIZE ORDER STATUS
    # --------------------------------------------------------
    #
    # Tracking status and Order status represent the same
    # delivery lifecycle. When tracking changes, update the
    # actual Order status as well.
    #
    # This is especially important for "Delivered" because
    # reviews are allowed only for delivered orders.
    # --------------------------------------------------------

    status_mapping = {
        "Pending": OrderStatus.PENDING,
        "Accepted": OrderStatus.ACCEPTED,
        "Preparing": OrderStatus.PREPARING,
        "Ready": OrderStatus.READY,
        "Picked Up": OrderStatus.PICKED_UP,
        "Out for Delivery": OrderStatus.OUT_FOR_DELIVERY,
        "Delivered": OrderStatus.DELIVERED,
        "Cancelled": OrderStatus.CANCELLED,
    }

    tracking_status = (
        data.status.value
        if hasattr(data.status, "value")
        else str(data.status)
    )

    if tracking_status in status_mapping:
        order.order_status = status_mapping[tracking_status]

    db.flush()
    db.commit()
    db.refresh(order)
    db.refresh(tracking)

    return tracking


# ============================================================
# GET ORDER TRACKING
# ============================================================

def get_order_tracking_service(
    db: Session,
    order_id: int,
    current_user: User,
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise ResourceNotFoundException(
            "Order not found"
        )

    if current_user.role == UserRole.CUSTOMER:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == order.customer_id,
                Customer.user_id == current_user.id,
            )
            .first()
        )

        if not customer:
            raise PermissionError(
                "You do not have permission to view this order tracking"
            )

    elif current_user.role == UserRole.DELIVERY_PARTNER:
        # DeliveryPartner is currently not directly
        # linked to User.
        pass

    elif current_user.role not in (
        UserRole.ADMIN,
        UserRole.RESTAURANT_OWNER,
        UserRole.RESTAURANT_STAFF,
    ):
        raise PermissionError(
            "You do not have permission to view order tracking"
        )

    return get_tracking_by_order(
        db,
        order_id,
    )