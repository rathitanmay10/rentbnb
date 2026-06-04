from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies.types import (
    DbDep,
    SuperAdminDep,
    TenantOrSuperAdminDep,
)
from app.schemas import TenantCreate, TenantListResponse, TenantResponse, TenantUpdate
from app.schemas.error import (
    BAD_REQUEST,
    CONFLICT,
    FORBIDDEN,
    NOT_FOUND,
)
from app.services import tenant_service

router = APIRouter(
    prefix="/tenants", tags=["Tenants"], responses={**NOT_FOUND, **FORBIDDEN}
)


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
    description="Create a new tenant (SUPER_ADMIN only).",
    responses={**CONFLICT},
)
async def create_tenant(
    tenant_data: TenantCreate,
    db: DbDep,
    current_user: SuperAdminDep,
):
    """
    Create a new tenant (SUPER_ADMIN only).
    - Tenant name must be unique (case-insensitive)
    """
    return await tenant_service.create_tenant(db, tenant_data)


@router.get(
    "/",
    response_model=TenantListResponse,
    summary="List all tenants",
    description="List all tenants with pagination.",
)
async def list_tenants(
    db: DbDep,
    current_user: TenantOrSuperAdminDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
):
    """List all tenants with pagination."""
    tenants, total = await tenant_service.get_tenants(db, current_user, skip, limit)

    return {"data": tenants, "total": total, "skip": skip, "limit": limit}


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID",
    description="Get a specific tenant by ID.",
)
async def get_tenant(
    tenant_id: UUID,
    db: DbDep,
    current_user: TenantOrSuperAdminDep,
):
    """Get a specific tenant by ID."""
    return await tenant_service.get_tenant(db, tenant_id, current_user)


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant",
    description="Update a tenant's name or status (SUPER_ADMIN only).",
    responses={**CONFLICT},
)
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    db: DbDep,
    current_user: SuperAdminDep,
):
    """
    Update a tenant (SUPER_ADMIN only).

    - Can update name and status
    - New name must be unique (case-insensitive)
    """
    return await tenant_service.update_tenant(db, tenant_id, tenant_data)


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete tenant",
    description="Soft delete a tenant and all associated users (SUPER_ADMIN only).",
    responses={**BAD_REQUEST},
)
async def delete_tenant(
    tenant_id: UUID,
    db: DbDep,
    current_user: SuperAdminDep,
) -> None:
    """
    Soft delete a tenant and all associated users (SUPER_ADMIN only).

    - Cascades to all users in the tenant
    - Data is not physically deleted, just marked as deleted
    """
    success = await tenant_service.soft_delete_tenant_cascade(db, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
