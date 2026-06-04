"""Reusable `Annotated` dependency aliases for routers.

Import these instead of repeating `param: T = Depends(...)` in path operations.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.dependencies.permissions import (
    require_roles,
    require_super_admin,
    require_tenant_or_super_admin,
)
from app.dependencies.tenant import get_tenant_id_from_header, get_tenant_user
from app.dependencies.user import get_current_user
from app.enums import UserRole
from app.models import User

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
TenantUserDep = Annotated[User, Depends(get_tenant_user)]
TenantIdDep = Annotated[UUID | None, Depends(get_tenant_id_from_header)]
SuperAdminDep = Annotated[User, Depends(require_super_admin)]
TenantOrSuperAdminDep = Annotated[User, Depends(require_tenant_or_super_admin)]
GuestUserDep = Annotated[User, Depends(require_roles(UserRole.GUEST))]
