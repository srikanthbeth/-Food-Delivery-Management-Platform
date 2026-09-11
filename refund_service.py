from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models.customer import Customer
from models.order import Order
from models.payment import Payment
from models.refund import Refund
from models.user import User
from repositories.refund_repository import (
    create_refund,
    get_all_refunds,
    get_refund_by_payment_id,
    get_refund_by_transaction_id,
)
from schemas.refund import RefundCreate
from utils.enums import (
    OrderStatus,
    PaymentStatus,
    PaymentTransactionStatus,
    UserRole,
)
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


REFUND_ROLES = (
    UserRole.ADMIN,
    UserRole.CUSTOMER,
)


def _validate_customer_order_access(
    db: Session,
    order: Order,
    current_user: User,
):
    if current_user.role != UserRole.CUSTOMER:
        return

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
            "You do not have permission to access this order"
        )


def cancel_order_service(
    db: Session,
    order_id: int,
    current_user: User,
):
    if current_user.role not in REFUND_ROLES:
        raise PermissionError(
            "You do not have permission to cancel this order"
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == order_id
        )
        .first()
    )

    if not order:
        raise ResourceNotFoundException(
            "Order not found"
        )

    _validate_customer_order_access(
        db,
        order,
        current_user,
    )

    if order.order_status == OrderStatus.DELIVERED:
        raise BusinessRuleException(
            "Delivered order cannot be cancelled"
        )

    if order.order_status == OrderStatus.CANCELLED:
        raise BusinessRuleException(
            "Order is already cancelled"
        )

    if order.order_status in (
        OrderStatus.READY,
        OrderStatus.PICKED_UP,
        OrderStatus.OUT_FOR_DELIVERY,
    ):
        raise BusinessRuleException(
            "Order cannot be cancelled at this stage"
        )

    order.order_status = OrderStatus.CANCELLED

    db.commit()
    db.refresh(order)

    return {
        "success": True,
        "message": "Order cancelled successfully",
        "order_id": order.id,
        "order_status": order.order_status,
    }


def create_refund_service(
    db: Session,
    payment_id: int,
    data: RefundCreate,
    current_user: User,
):
    if current_user.role not in REFUND_ROLES:
        raise PermissionError(
            "You do not have permission to process refund"
        )

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )

    if not payment:
        raise ResourceNotFoundException(
            "Payment not found"
        )

    order = (
        db.query(Order)
        .filter(
            Order.id == payment.order_id
        )
        .first()
    )

    if not order:
        raise ResourceNotFoundException(
            "Order not found"
        )

    _validate_customer_order_access(
        db,
        order,
        current_user,
    )

    if payment.payment_status != PaymentTransactionStatus.SUCCESSFUL:
        raise BusinessRuleException(
            "Only successful payments can be refunded"
        )

    if order.order_status != OrderStatus.CANCELLED:
        raise BusinessRuleException(
            "Order must be cancelled before refund"
        )

    existing_refund = get_refund_by_payment_id(
        db,
        payment_id,
    )

    if existing_refund:
        raise BusinessRuleException(
            "Refund already exists for this payment"
        )

    existing_transaction = (
        get_refund_by_transaction_id(
            db,
            data.refund_transaction_id,
        )
    )

    if existing_transaction:
        raise BusinessRuleException(
            "Refund transaction ID already exists"
        )

    if data.amount > payment.amount:
        raise BusinessRuleException(
            "Refund amount cannot exceed payment amount"
        )

    refund = Refund(
        payment_id=payment.id,
        order_id=order.id,
        amount=data.amount,
        reason=data.reason,
        refund_transaction_id=data.refund_transaction_id,
        refund_status=PaymentTransactionStatus.REFUNDED,
        refunded_at=datetime.utcnow(),
    )

    db.add(refund)

    if data.amount == payment.amount:
        payment.payment_status = (
            PaymentTransactionStatus.REFUNDED
        )

        order.payment_status = PaymentStatus.REFUNDED

    db.commit()
    db.refresh(refund)

    return refund


def get_refunds_service(
    db: Session,
    current_user: User,
):
    if current_user.role == UserRole.ADMIN:
        return get_all_refunds(db)

    if current_user.role != UserRole.CUSTOMER:
        raise PermissionError(
            "You do not have permission to view refunds"
        )

    refunds = (
        db.query(Refund)
        .join(
            Order,
            Refund.order_id == Order.id,
        )
        .join(
            Customer,
            Order.customer_id == Customer.id,
        )
        .filter(
            Customer.user_id == current_user.id
        )
        .order_by(
            Refund.id.desc()
        )
        .all()
    )

    return refunds