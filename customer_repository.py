from sqlalchemy.orm import Session

from models.customer import Customer


def create_customer(
    db: Session,
    customer: Customer,
) -> Customer:
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customer_by_id(
    db: Session,
    customer_id: int,
) -> Customer | None:
    return (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )


def get_customer_by_email(
    db: Session,
    email: str,
) -> Customer | None:
    return (
        db.query(Customer)
        .filter(Customer.email == email)
        .first()
    )