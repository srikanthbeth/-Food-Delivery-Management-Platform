from sqlalchemy.orm import Session

from models.customer import Customer
from repositories.customer_repository import (
    create_customer,
    get_customer_by_email,
    get_customer_by_id,
)
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


def create_customer_service(
    db: Session,
    customer_data,
    current_user,
) -> Customer:

    # Check whether this user already has a customer profile
    existing_customer = (
        db.query(Customer)
        .filter(Customer.user_id == current_user.id)
        .first()
    )

    if existing_customer:
        raise BusinessRuleException(
            "Customer profile already exists for this user"
        )

    # Check duplicate email
    existing_email = get_customer_by_email(
        db,
        customer_data.email,
    )

    if existing_email:
        raise BusinessRuleException(
            "Customer email already exists"
        )

    customer = Customer(
        user_id=current_user.id,
        name=customer_data.name,
        email=customer_data.email,
        phone=customer_data.phone,
    )

    return create_customer(
        db,
        customer,
    )


def get_customer_service(
    db: Session,
    customer_id: int,
) -> Customer:

    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if not customer:
        raise ResourceNotFoundException(
            "Customer not found"
        )

    return customer