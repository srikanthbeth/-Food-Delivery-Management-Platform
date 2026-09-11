from sqlalchemy.orm import Session

from models.payment import Payment


def create_payment(
    db: Session,
    payment: Payment,
) -> Payment:

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_payment_by_id(
    db: Session,
    payment_id: int,
) -> Payment | None:

    return (
        db.query(Payment)
        .filter(
            Payment.id == payment_id
        )
        .first()
    )


def get_payment_by_order_id(
    db: Session,
    order_id: int,
) -> Payment | None:

    return (
        db.query(Payment)
        .filter(
            Payment.order_id == order_id
        )
        .first()
    )


def get_payment_by_transaction_id(
    db: Session,
    transaction_id: str,
) -> Payment | None:

    return (
        db.query(Payment)
        .filter(
            Payment.transaction_id == transaction_id
        )
        .first()
    )


def update_payment(
    db: Session,
    payment: Payment,
    **fields,
) -> Payment:

    for field, value in fields.items():
        setattr(
            payment,
            field,
            value,
        )

    db.commit()
    db.refresh(payment)

    return payment