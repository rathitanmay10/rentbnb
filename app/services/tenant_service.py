from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, property_crud, tenant_crud, user_crud
from app.enums import UserRole
from app.models import Tenant, User
from app.schemas import TenantCreate, TenantUpdate


async def create_tenant(db: AsyncSession, tenant_data: TenantCreate) -> Tenant:
    """
    Create a new tenant with case-insensitive uniqueness check.
    """
    existing_tenant = await tenant_crud.get_tenant_by_name_ci(
        db, tenant_data.name.lower()
    )
    if existing_tenant:
        raise ValueError("Tenant with this name already exists")

    tenant = await tenant_crud.create_tenant(db, tenant_data.name)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e
    return tenant


async def get_tenant(db: AsyncSession, tenant_id: UUID) -> Tenant | None:
    """Get a tenant by ID."""
    return await tenant_crud.get_tenant(db, tenant_id)


async def get_tenants(
    db: AsyncSession, current_user: User, skip: int = 0, limit: int = 10
) -> tuple[list[Tenant], int]:
    """Get all tenants with pagination.

    For TENANT_ADMIN: Returns their own tenant if skip=0, empty list if skip>=1.
    For SUPER_ADMIN: Returns paginated list of all tenants.
    """
    if current_user.role == UserRole.TENANT_ADMIN:
        tenant = await tenant_crud.get_tenant(db, current_user.tenant_id)
        if skip >= 1:
            return [], 1
        return [tenant], 1
    tenants = await tenant_crud.get_tenants(db, skip, limit)
    total = await tenant_crud.get_tenants_count(db)

    return tenants, total


async def update_tenant(
    db: AsyncSession, tenant_id: UUID, tenant_data: TenantUpdate
) -> Tenant | None:
    """
    Update a tenant.
    """
    updates = tenant_data.model_dump(exclude_unset=True)
    if tenant_data.name is not None:
        existing_tenant = await tenant_crud.get_tenant_by_name_ci(
            db, tenant_data.name.lower()
        )
        if existing_tenant:
            raise ValueError("Tenant with this name already exists")
    try:
        tenant = await tenant_crud.update_tenant(db, tenant_id, **updates)
        await db.commit()
        return tenant
    except Exception as e:
        await db.rollback()
        raise e


async def soft_delete_tenant_cascade(db: AsyncSession, tenant_id: UUID) -> bool:
    """
    Soft delete tenant and all associated users and properties.
    """
    tenant = await tenant_crud.get_tenant(db, tenant_id)
    if not tenant:
        return False
    booking = await booking_crud.get_bookings(
        db, tenant_id=tenant_id, check_in=datetime.now(UTC).date(), active=True
    )
    if booking:
        raise ValueError("Tenant has future bookings, cannot delete")

    await user_crud.soft_delete_users_by_tenant(db, tenant_id)
    await property_crud.soft_delete_properties_by_tenant(db, tenant_id)
    success = await tenant_crud.soft_delete_tenant(db, tenant_id)
    if success:
        await db.commit()
    return success
