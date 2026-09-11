from sqlalchemy.orm import Session

from models.address import Address


def create_address(
    db: Session,
    address: Address,
) -> Address:
    db.add(address)
    db.commit()
    db.refresh(address)

    return address


def get_address_by_id(
    db: Session,
    address_id: int,
) -> Address | None:
    return (
        db.query(Address)
        .filter(Address.id == address_id)
        .first()
    )


def get_customer_addresses(
    db: Session,
    customer_id: int,
) -> list[Address]:
    return (
        db.query(Address)
        .filter(Address.customer_id == customer_id)
        .order_by(
            Address.is_default.desc(),
            Address.id.asc(),
        )
        .all()
    )


def unset_customer_default_addresses(
    db: Session,
    customer_id: int,
) -> None:
    (
        db.query(Address)
        .filter(
            Address.customer_id == customer_id,
            Address.is_default.is_(True),
        )
        .update(
            {
                Address.is_default: False,
            },
            synchronize_session=False,
        )
    )


def update_address(
    db: Session,
    address: Address,
    data: dict,
) -> Address:
    for field, value in data.items():
        setattr(address, field, value)

    db.commit()
    db.refresh(address)

    return address