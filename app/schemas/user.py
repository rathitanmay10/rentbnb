from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.enums import UserRole
from app.utils.validators import (
    validate_first_name,
    validate_last_name,
    validate_password,
    validate_username,
)


class UserBase(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class UserCreate(UserBase):
    username: str
    email: EmailStr = Field(max_length=255)
    password: str
    tenant_id: UUID | None = None
    role: UserRole = UserRole.GUEST
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str) -> str:
        return validate_username(v)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        return validate_password(v)

    @field_validator("first_name")
    @classmethod
    def _validate_first_name(cls, v: str | None) -> str | None:
        return validate_first_name(v)

    @field_validator("last_name")
    @classmethod
    def _validate_last_name(cls, v: str | None) -> str | None:
        return validate_last_name(v)


class SuperAdminUserCreate(UserCreate):
    tenant_id: UUID
    role: UserRole = UserRole.SUPER_ADMIN


class UserUpdate(BaseModel):
    is_active: bool | None = None
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("first_name")
    @classmethod
    def _validate_first_name(cls, v: str | None) -> str | None:
        return validate_first_name(v)

    @field_validator("last_name")
    @classmethod
    def _validate_last_name(cls, v: str | None) -> str | None:
        return validate_last_name(v)


class UserSelfUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("first_name")
    @classmethod
    def _validate_first_name(cls, v: str | None) -> str | None:
        return validate_first_name(v)

    @field_validator("last_name")
    @classmethod
    def _validate_last_name(cls, v: str | None) -> str | None:
        return validate_last_name(v)


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    first_name: str | None
    last_name: str | None
    role: UserRole
    tenant_id: UUID | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[UserResponse]
