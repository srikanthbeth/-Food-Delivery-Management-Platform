from sqlalchemy.orm import Session

from models.refund import Refund


def create_refund(
    db: Session,
    refund: Refund,
) -> Refund:

    db.add(refund)
    db.commit()
    db.refresh(refund)

    return refund


def get_refund_by_id(
    db: Session,
    refund_id: int,
) -> Refund | None:

    return (
        db.query(Refund)
        .filter(
            Refund.id == refund_id
        )
        .first()
    )


def get_refund_by_payment_id(
    db: Session,
    payment_id: int,
) -> Refund | None:

    return (
        db.query(Refund)
        .filter(
            Refund.payment_id == payment_id
        )
        .first()
    )


def get_refund_by_transaction_id(
    db: Session,
    refund_transaction_id: str,
) -> Refund | None:

    return (
        db.query(Refund)
        .filter(
            Refund.refund_transaction_id
            == refund_transaction_id
        )
        .first()
    )


def get_all_refunds(
    db: Session,
) -> list[Refund]:

    return (
        db.query(Refund)
        .order_by(
            Refund.id.desc()
        )
        .all()
    )