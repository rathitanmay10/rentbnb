from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums import TenantStatus
from app.utils.validators import validate_tenant_name


class TenantBase(BaseModel):
    name: str | None = None


class TenantCreate(TenantBase):
    name: str = Field(max_length=255)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        return validate_tenant_name(v)


class TenantUpdate(TenantBase):
    status: TenantStatus | None = None
    name: str | None = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str | None) -> str | None:
        return validate_tenant_name(v)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: TenantStatus | None) -> TenantStatus | None:
        if v is None:
            raise ValueError("Tenant Status cannot be null")
        return v


class TenantResponse(BaseModel):
    id: UUID
    name: str
    status: TenantStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[TenantResponse]
