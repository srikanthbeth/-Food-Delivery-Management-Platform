from pydantic import BaseModel, ConfigDict, EmailStr, Field

from utils.enums import UserRole


class RegisterRequest(BaseModel):

    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        min_length=10,
        max_length=20,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )

    role: UserRole = UserRole.CUSTOMER


class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )


class RefreshRequest(BaseModel):

    refresh_token: str


class ChangePasswordRequest(BaseModel):

    current_password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )


class UserResponse(BaseModel):

    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class TokenResponse(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):

    message: str

class UserStatusRequest(BaseModel):
    is_active: bool

class UserStatusUpdate(BaseModel):
    is_active: bool

class UserStatusResponse(BaseModel):
    id: int
    is_active: bool