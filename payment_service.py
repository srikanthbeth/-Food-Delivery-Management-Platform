from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from models.customer import Customer
from models.order import Order
from models.payment import Payment
from models.user import User
from repositories.payment_repository import (
    create_payment,
    get_payment_by_id,
    get_payment_by_order_id,
    get_payment_by_transaction_id,
)
from schemas.payment import PaymentCreate
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


MANAGE_ROLES = (
    UserRole.ADMIN,
    UserRole.CUSTOMER,
)


def create_payment_service(
    db: Session,
    order_id: int,
    data: PaymentCreate,
    current_user: User,
):

    if current_user.role not in MANAGE_ROLES:
        raise PermissionError(
            "You do not have permission to make payment"
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

    # Customer can pay only their own order.
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
                "You do not have permission to pay for this order"
            )

    # Cancelled orders cannot be paid.
    if order.order_status == OrderStatus.CANCELLED:

        raise BusinessRuleException(
            "Cancelled order cannot be paid"
        )

    # Check whether order already has a payment.
    existing_payment = get_payment_by_order_id(
        db,
        order_id,
    )

    if existing_payment:

        if (
            existing_payment.payment_status
            == PaymentTransactionStatus.SUCCESSFUL
        ):
            raise BusinessRuleException(
                "Order has already been paid"
            )

        raise BusinessRuleException(
            "Payment already exists for this order"
        )

    # Amount must match order total exactly.
    if data.amount != order.total_amount:

        raise BusinessRuleException(
            f"Payment amount must match order total "
            f"{order.total_amount}"
        )

    # Transaction ID must be unique.
    existing_transaction = (
        get_payment_by_transaction_id(
            db,
            data.transaction_id,
        )
    )

    if existing_transaction:

        raise BusinessRuleException(
            "Transaction ID already exists"
        )

    payment_status = (
        PaymentTransactionStatus.SUCCESSFUL
    )

    payment = Payment(
        order_id=order.id,
        amount=data.amount,
        payment_method=data.payment_method,
        transaction_id=data.transaction_id,
        payment_status=payment_status,
        paid_at=datetime.utcnow(),
    )

    db.add(payment)

    # Successful payment updates order payment status.
    order.payment_status = PaymentStatus.PAID

    db.commit()

    db.refresh(payment)

    return payment


def get_payment_service(
    db: Session,
    payment_id: int,
    current_user: User,
):

    if current_user.role not in MANAGE_ROLES:

        raise PermissionError(
            "You do not have permission to view payment"
        )

    payment = get_payment_by_id(
        db,
        payment_id,
    )

    if not payment:

        raise ResourceNotFoundException(
            "Payment not found"
        )

    if current_user.role == UserRole.CUSTOMER:

        customer = (
            db.query(Customer)
            .filter(
                Customer.id == payment.order.customer_id,
                Customer.user_id == current_user.id,
            )
            .first()
        )

        if not customer:

            raise PermissionError(
                "You do not have permission to view this payment"
            )

    return payment


def get_order_payment_service(
    db: Session,
    order_id: int,
    current_user: User,
):

    if current_user.role not in MANAGE_ROLES:

        raise PermissionError(
            "You do not have permission to view payment"
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
                "You do not have permission to view this payment"
            )

    payment = get_payment_by_order_id(
        db,
        order_id,
    )

    if not payment:

        raise ResourceNotFoundException(
            "Payment not found"
        )

    return payment