from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    """Get a user by ID."""
    return await db.get(User, user_id)


async def get_user_by_email_ci(
    db: AsyncSession, email: str, tenant_id: UUID | None = None
) -> User | None:
    """Get user by email (case-insensitive) and tenant. Email should be pre-lowercased."""
    query = select(User).where(User.email == email, User.is_deleted.is_(False))
    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)
    else:
        query = query.where(User.tenant_id.is_(None))

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_by_username_ci(db: AsyncSession, username: str) -> User | None:
    """Get user by username (case-insensitive). Username should be pre-lowercased."""
    query = select(User).where(User.username == username, User.is_deleted.is_(False))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 10, tenant_id: UUID | None = None
) -> list[User]:
    """Get users with pagination. Optionally filter by tenant_id."""
    query = select(User).where(User.is_deleted.is_(False))

    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)

    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_users_count(db: AsyncSession, tenant_id: UUID | None = None) -> int:
    """Get total count of active users. Optionally filter by tenant_id."""
    query = select(func.count(User.id)).where(User.is_deleted.is_(False))

    if tenant_id:
        query = query.where(User.tenant_id == tenant_id)

    result = await db.execute(query)
    return result.scalar_one()


async def create_user(db: AsyncSession, user_dict: dict) -> User:
    """Create a new user from dictionary."""
    user = User(**user_dict)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: UUID, **updates) -> User | None:
    """Update a user with given fields."""
    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        return None

    for field, value in updates.items():
        if hasattr(user, field):
            setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """Soft delete a user."""
    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        return False

    user.soft_delete()
    await db.flush()
    return True


async def soft_delete_users_by_tenant(db: AsyncSession, tenant_id: UUID) -> int:
    """Soft delete all users belonging to a tenant. Returns count of deleted users."""
    query = select(User).where(User.tenant_id == tenant_id, User.is_deleted.is_(False))
    result = await db.execute(query)
    users = result.scalars().all()

    count = 0
    for user in users:
        user.soft_delete()
        count += 1

    await db.flush()
    return count


async def increment_token_version(db: AsyncSession, user_id: UUID) -> bool:
    """Increment user's token version (invalidates all tokens). Returns True if successful."""
    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        return False

    user.token_version += 1
    await db.flush()
    return True
