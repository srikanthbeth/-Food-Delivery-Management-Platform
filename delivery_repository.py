from sqlalchemy.orm import Session

from models.delivery_partner import DeliveryPartner


def create_delivery_partner(
    db: Session,
    delivery_partner: DeliveryPartner,
) -> DeliveryPartner:

    db.add(delivery_partner)
    db.commit()
    db.refresh(delivery_partner)

    return delivery_partner


def get_delivery_partner_by_id(
    db: Session,
    delivery_partner_id: int,
) -> DeliveryPartner | None:

    return (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.id
            == delivery_partner_id
        )
        .first()
    )


def get_delivery_partner_by_phone(
    db: Session,
    phone: str,
) -> DeliveryPartner | None:

    return (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.phone == phone
        )
        .first()
    )


def get_delivery_partner_by_vehicle_number(
    db: Session,
    vehicle_number: str,
) -> DeliveryPartner | None:

    return (
        db.query(DeliveryPartner)
        .filter(
            DeliveryPartner.vehicle_number
            == vehicle_number
        )
        .first()
    )


def get_all_delivery_partners(
    db: Session,
) -> list[DeliveryPartner]:

    return (
        db.query(DeliveryPartner)
        .order_by(
            DeliveryPartner.id.desc()
        )
        .all()
    )


def update_delivery_partner(
    db: Session,
    delivery_partner: DeliveryPartner,
    **fields,
) -> DeliveryPartner:

    for field, value in fields.items():
        setattr(
            delivery_partner,
            field,
            value,
        )

    db.commit()
    db.refresh(delivery_partner)

    return delivery_partner