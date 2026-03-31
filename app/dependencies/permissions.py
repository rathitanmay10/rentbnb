"""Role-based access control dependencies."""

from fastapi import Depends, HTTPException, status

from app.dependencies.user import get_current_user
from app.enums import UserRole
from app.models import User


def require_roles(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control.

    Usage:
        @router.get("/admin")
        async def admin_only(
            user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN))
        ):
            ...

    Args:
        *allowed_roles: One or more UserRole enums

    Returns:
        Dependency function that validates user role
    """

    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return check_role


async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require SUPER_ADMIN role.

    Raises:
        HTTPException: 403 if user is not SUPER_ADMIN
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


async def require_tenant_or_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require TENANT_ADMIN or SUPER_ADMIN role.

    Raises:
        HTTPException: 403 if user is not TENANT_ADMIN or SUPER_ADMIN
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
