"""Tenant-related dependencies."""

from fastapi import Depends, HTTPException, status

from app.dependencies.user import get_current_user
from app.enums import TenantStatus
from app.models import Tenant, User


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
            detail="Tenant not found",
        )

    if tenant.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant has been deleted",
        )

    if tenant.status == TenantStatus.INACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is inactive",
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
