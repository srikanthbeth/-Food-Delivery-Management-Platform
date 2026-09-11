from sqlalchemy.orm import Session

from models.user import User
from repositories.user_repository import (
    create_user,
    get_user_by_email,
    get_user_by_id,
)
from schemas.auth import (
    ChangePasswordRequest,
    RegisterRequest,
)
from utils.exceptions import (
    AuthenticationException,
    BusinessRuleException,
)
from utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

from utils.enums import UserRole
from sqlalchemy.orm import Session

from models.user import User
from repositories.user_repository import get_user_by_id
from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)

def register_user(
    db: Session,
    data: RegisterRequest,
) -> User:

    existing_user = get_user_by_email(
        db,
        data.email,
    )

    if existing_user:
        raise BusinessRuleException(
            "Email already registered"
        )

    user = User(
        full_name=data.full_name.strip(),
        email=data.email.lower(),
        phone=data.phone,
        password_hash=hash_password(
            data.password
        ),
        role=data.role,
        is_active=True,
    )

    return create_user(
        db,
        user,
    )


def login_user(
    db: Session,
    email: str,
    password: str,
) -> dict:

    user = get_user_by_email(
        db,
        email,
    )

    if not user:
        raise AuthenticationException(
            "Invalid email or password"
        )

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise AuthenticationException(
            "Invalid email or password"
        )

    if not user.is_active:
        raise AuthenticationException(
            "User account is inactive"
        )

    access_token = create_access_token(
        user.id,
        user.role.value,
    )

    refresh_token = create_refresh_token(
        user.id,
        user.role.value,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(
    db: Session,
    user_id: int,
) -> dict:

    user = get_user_by_id(
        db,
        user_id,
    )

    if not user:
        raise AuthenticationException(
            "User not found"
        )

    if not user.is_active:
        raise AuthenticationException(
            "User account is inactive"
        )

    access_token = create_access_token(
        user.id,
        user.role.value,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


def change_password(
    db: Session,
    user: User,
    data: ChangePasswordRequest,
) -> None:

    if not verify_password(
        data.current_password,
        user.password_hash,
    ):
        raise AuthenticationException(
            "Current password is incorrect"
        )

    if (
        data.current_password
        == data.new_password
    ):
        raise BusinessRuleException(
            "New password must be different"
        )

    user.password_hash = hash_password(
        data.new_password
    )

    db.commit()

def change_user_status(
    db: Session,
    user_id: int,
    is_active: bool,
    current_user: User,
):
    user = get_user_by_id(db, user_id)

    if not user:
        raise ResourceNotFoundException("User not found")

    # Admin cannot deactivate their own account
    if user.id == current_user.id and not is_active:
        raise BusinessRuleException(
            "Admin cannot deactivate their own account"
        )

    user.is_active = is_active

    db.commit()
    db.refresh(user)

    return user