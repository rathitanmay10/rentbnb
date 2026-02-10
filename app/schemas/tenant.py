from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.enums import TenantStatus
from app.utils.validators import (
    validate_password,
    validate_tenant_name,
    validate_username,
)


class TenantBase(BaseModel):
    name: str | None = None


class TenantCreate(TenantBase):
    name: str

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str):
        return validate_tenant_name(v)


class TenantUpdate(TenantBase):
    status: TenantStatus | None = None

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str | None):
        return validate_tenant_name(v)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: TenantStatus | None):
        if v is None:
            raise ValueError("Tenant Status cannot be null")
        return v


class TenantRegistrationSchema(BaseModel):
    """Schema for tenant registration with admin user."""

    company_name: str
    admin_username: str
    admin_email: str
    admin_password: str

    @field_validator("company_name")
    @classmethod
    def _validate_company_name(cls, v: str):
        return validate_tenant_name(v)

    @field_validator("admin_username")
    @classmethod
    def _validate_username(cls, v: str):
        return validate_username(v)

    @field_validator("admin_password")
    @classmethod
    def _validate_password(cls, v: str):
        return validate_password(v)


class TenantResponse(BaseModel):
    id: UUID
    name: str
    status: TenantStatus
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[TenantResponse]
