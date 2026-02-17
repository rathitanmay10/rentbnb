from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.dependencies import require_super_admin, require_tenant_or_super_admin
from app.enums import UserRole
from app.models import User
from app.schemas import TenantCreate, TenantListResponse, TenantResponse, TenantUpdate
from app.services import tenant_service

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
    description="Create a new tenant (SUPER_ADMIN only).",
)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Create a new tenant (SUPER_ADMIN only).
    - Tenant name must be unique (case-insensitive)
    """
    try:
        tenant = await tenant_service.create_tenant(db, tenant_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return tenant


@router.get(
    "/",
    response_model=TenantListResponse,
    summary="List all tenants",
    description="List all tenants with pagination.",
)
async def list_tenants(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of records to return"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_tenant_or_super_admin),
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_tenant_or_super_admin),
):
    """Get a specific tenant by ID."""
    if (
        current_user.role == UserRole.TENANT_ADMIN
        and not tenant_id == current_user.tenant_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    tenant = await tenant_service.get_tenant(db, tenant_id)
    if not tenant or tenant.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
        )
    return tenant


@router.patch(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant",
    description="Update a tenant's name or status (SUPER_ADMIN only).",
)
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Update a tenant (SUPER_ADMIN only).

    - Can update name and status
    - New name must be unique (case-insensitive)
    """
    try:
        tenant = await tenant_service.update_tenant(db, tenant_id, tenant_data)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return tenant


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete tenant",
    description="Soft delete a tenant and all associated users (SUPER_ADMIN only).",
)
async def delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Soft delete a tenant and all associated users (SUPER_ADMIN only).

    - Cascades to all users in the tenant
    - Data is not physically deleted, just marked as deleted
    """
    try:
        await tenant_service.soft_delete_tenant_cascade(db, tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return
