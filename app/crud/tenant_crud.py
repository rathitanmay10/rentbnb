from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant


async def get_tenant(db: AsyncSession, tenant_id: UUID) -> Tenant | None:
    """Get a tenant by ID."""
    return await db.get(Tenant, tenant_id)


async def get_tenant_by_name_ci(db: AsyncSession, name: str) -> Tenant | None:
    """Get tenant by name (case-insensitive). Name should be pre-lowercased."""
    query = select(Tenant).where(func.lower(Tenant.name) == name)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tenants(db: AsyncSession, skip: int = 0, limit: int = 10) -> list[Tenant]:
    """Get all tenants with pagination."""
    query = (
        select(Tenant)
        .where(Tenant.is_deleted.is_(False))
        .order_by(Tenant.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tenants_count(db: AsyncSession) -> int:
    """Get total count of active tenants."""
    query = select(func.count(Tenant.id)).where(Tenant.is_deleted.is_(False))
    result = await db.execute(query)
    return result.scalar_one()


async def create_tenant(db: AsyncSession, name: str) -> Tenant:
    """Create a new tenant."""
    tenant = Tenant(name=name)
    db.add(tenant)
    await db.flush()
    await db.refresh(tenant)
    return tenant


async def update_tenant(db: AsyncSession, tenant_id: UUID, **updates) -> Tenant | None:
    """Update a tenant with given fields."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant or tenant.is_deleted:
        return None

    for field, value in updates.items():
        if hasattr(tenant, field):
            setattr(tenant, field, value)

    await db.flush()
    await db.refresh(tenant)
    return tenant


async def soft_delete_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
    """Soft delete a tenant."""
    tenant = await db.get(Tenant, tenant_id)
    if not tenant or tenant.is_deleted:
        return False

    tenant.soft_delete()
    await db.flush()
    return True
