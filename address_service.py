from sqlalchemy.orm import Session

from models.address import Address
from repositories.address_repository import (
    create_address,
    get_address_by_id,
    get_customer_addresses,
    unset_customer_default_addresses,
    update_address,
)
from repositories.customer_repository import get_customer_by_id
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


def validate_customer_access(
    customer,
    current_user,
):
    # Admin can manage any customer
    if current_user.role.value == "Admin":
        return

    # Customer can manage only their own customer record
    # Customer's email is used to identify ownership.
    if current_user.role.value == "Customer":
        if customer.user_id != current_user.id:
            raise BusinessRuleException(
                "You can only manage your own addresses"
            )
        return

    raise PermissionError(
        "Insufficient permissions"
    )


def create_address_service(
    db: Session,
    customer_id: int,
    address_data,
    current_user,
):
    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if not customer:
        raise ResourceNotFoundException(
            "Customer not found"
        )

    validate_customer_access(
        customer,
        current_user,
    )

    # If this is the first address, automatically make it default.
    existing_addresses = get_customer_addresses(
        db,
        customer_id,
    )

    should_be_default = address_data.is_default

    if not existing_addresses:
        should_be_default = True

    if should_be_default:
        unset_customer_default_addresses(
            db,
            customer_id,
        )

    address = Address(
        customer_id=customer_id,
        address_line=address_data.address_line,
        city=address_data.city,
        pincode=address_data.pincode,
        latitude=address_data.latitude,
        longitude=address_data.longitude,
        address_type=address_data.address_type,
        is_default=should_be_default,
    )

    return create_address(
        db,
        address,
    )


def get_customer_addresses_service(
    db: Session,
    customer_id: int,
    current_user,
):
    customer = get_customer_by_id(
        db,
        customer_id,
    )

    if not customer:
        raise ResourceNotFoundException(
            "Customer not found"
        )

    validate_customer_access(
        customer,
        current_user,
    )

    return get_customer_addresses(
        db,
        customer_id,
    )


def update_address_service(
    db: Session,
    address_id: int,
    update_data,
    current_user,
):
    address = get_address_by_id(
        db,
        address_id,
    )

    if not address:
        raise ResourceNotFoundException(
            "Address not found"
        )

    customer = get_customer_by_id(
        db,
        address.customer_id,
    )

    if not customer:
        raise ResourceNotFoundException(
            "Customer not found"
        )

    validate_customer_access(
        customer,
        current_user,
    )

    data = update_data.model_dump(
        exclude_unset=True
    )

    if not data:
        raise BusinessRuleException(
            "No fields provided for update"
        )

    if data.get("is_default") is True:
        unset_customer_default_addresses(
            db,
            customer.id,
        )

    return update_address(
        db,
        address,
        data,
    )