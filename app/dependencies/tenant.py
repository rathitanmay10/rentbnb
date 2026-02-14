"""Tenant-related dependencies."""

from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from app.constants.messages import NOT_FOUND
from app.dependencies.user import get_current_user
from app.enums import TenantStatus
from app.models import Property, Tenant, User


async def get_current_tenant(current_user: User = Depends(get_current_user)) -> Tenant:
    """
    Get current user's tenant and validate it's active.

    Validates:
    - User has a tenant
    - Tenant exists
    - Tenant is not soft-deleted
    - Tenant status is active

    Raises:
        HTTPException: 403 for invalid/inactive tenant, 404 if not found
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no tenant",
        )

    tenant = current_user.tenant
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Tenant not found",
        )

    if tenant.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User Tenant has been deleted",
        )

    if tenant.status == TenantStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User Tenant is inactive",
        )

    return tenant


def verify_tenant_access(current_user: User, target_user: User) -> None:
    """
    Verify if current_user can access the target_user.
    Raises 404 (Not Found) if access is denied to avoid leaking existence.
    """
    from app.enums import UserRole  # Avoid circular import if possible

    # 1. User accessing themselves -> ALLOW
    if current_user.id == target_user.id:
        return

    # 2. Super Admin -> ALLOW (assuming they manage users)
    if current_user.role == UserRole.SUPER_ADMIN:
        return

    # 3. Guest (No Tenant, Not Super Admin) -> DENY
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # 4. Different Tenant -> DENY
    if current_user.tenant_id != target_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )


def verify_tenant_admin_management(current_user: User, target_user: User) -> None:
    """
    Verify if current_user (Tenant Admin) can manage target_user.
    """
    from app.enums import UserRole

    # Must be same tenant
    verify_tenant_access(current_user, target_user)

    # Tenant Admin cannot manage other Tenant Admins (unless self, handled above)
    # or Super Admins (impossible by tenant check usually, but good to be safe)
    if target_user.role in [UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage this user",
        )


def get_tenant_id_from_header(
    x_tenant_id: str | None = Header(None, alias="x-tenant-id"),
) -> UUID | None:
    """
    Extract tenant ID from header.
    Returns UUID if present and valid, else None.
    Raises 400 if invalid UUID format.
    """
    if not x_tenant_id:
        return None

    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid x-tenant-id header format",
        )


def verify_tenant_property_access(current_user: User, property: Property) -> None:
    """
    Verify if current_user can access the property.
    Raises 404 (Not Found) if access is denied to avoid leaking existence.
    """

    if current_user.tenant_id == property.tenant_id:
        return

    if current_user.tenant_id != property.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)


def get_tenant_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user's tenant and validate it's active.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    tenant = get_current_tenant(current_user)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User Tenant not found"
        )
    return current_user
