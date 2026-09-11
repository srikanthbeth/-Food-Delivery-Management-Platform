from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:

    return db.scalar(
        select(User).where(
            User.id == user_id
        )
    )


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:

    return db.scalar(
        select(User).where(
            User.email == email.lower()
        )
    )


def create_user(
    db: Session,
    user: User,
) -> User:

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def update_user_status(
    db: Session,
    user: User,
    is_active: bool,
) -> User:

    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return user