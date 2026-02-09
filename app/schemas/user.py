from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from app.enums import UserRole
from app.utils.validators import validate_password, validate_username


class UserBase(BaseModel):
    username: str | None = None
    email: EmailStr | None = None


class UserCreate(UserBase):
    username: str
    email: EmailStr
    password: str
    tenant_id: UUID | None = None
    role: UserRole = UserRole.GUEST

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v):
        return validate_username(v)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v):
        return validate_password(v)


class SuperAdminUserCreate(UserCreate):
    tenant_id: UUID
    role: UserRole = UserRole.ADMIN


class UserUpdate(UserBase):
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str | None):
        if v is None:
            return v
        return validate_username(v)


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    tenant_id: UUID | None
    is_active: bool
    is_verified: bool
    token_version: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[UserResponse]
