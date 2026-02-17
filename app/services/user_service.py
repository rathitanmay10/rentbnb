from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, user_crud
from app.enums import UserRole
from app.models import User
from app.schemas import UserCreate, UserSelfUpdate, UserUpdate
from app.utils.password import hash_password


async def create_user(
    db: AsyncSession, user_data: UserCreate, tenant_id: UUID | None = None
) -> User:
    """
    Create a new user with case-insensitive uniqueness checks.

    Raises:
        ValueError: If email or username already exists, or tenant is invalid
    """
    # Check email uniqueness (case-insensitive) scoped to tenant
    existing_email = await user_crud.get_user_by_email_ci(
        db, user_data.email.lower(), tenant_id
    )
    if existing_email:
        raise ValueError("Email already registered")

    # Check username uniqueness (case-insensitive) scoped to tenant
    existing_username = await user_crud.get_user_by_username_ci(
        db, user_data.username.lower(), tenant_id
    )
    if existing_username:
        raise ValueError("Username already taken")

    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["hashed_password"] = hash_password(user_data.password)

    user_dict["username"] = user_dict["username"].lower()
    user_dict["email"] = user_dict["email"].lower()

    user = await user_crud.create_user(db, user_dict)
    await db.commit()
    return user


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    """Get a user by ID."""
    return await user_crud.get_user(db, user_id)


async def get_user_by_email(
    db: AsyncSession, email: str, tenant_id: UUID | None = None
) -> User | None:
    """Get user by email (case-insensitive) and tenant."""
    return await user_crud.get_user_by_email_ci(db, email.lower(), tenant_id)


async def get_users(
    db: AsyncSession, skip: int, limit: int, current_user: User
) -> tuple[list[User], int]:
    """
    Get users with tenant filtering based on user role.

    - SUPER_ADMIN sees all users
    - Other roles only see their tenant's users
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        tenant_id = None
    else:
        tenant_id = current_user.tenant_id

    users = await user_crud.get_users(db, skip, limit, tenant_id)
    count = await user_crud.get_users_count(db, tenant_id)
    return users, count


async def update_user(
    db: AsyncSession, user_id: UUID, user_data: UserUpdate | UserSelfUpdate
) -> User | None:
    """
    Update a user.
    """

    updates = user_data.model_dump(exclude_unset=True)

    user = await user_crud.update_user(db, user_id, **updates)
    await db.commit()
    return user


async def delete_user(db: AsyncSession, target_user: User) -> bool:
    """Soft delete a user."""
    if target_user.role == UserRole.SUPER_ADMIN:
        raise ValueError("Super admin cannot be deleted")
    if target_user.role in [UserRole.TENANT_ADMIN, UserRole.MANAGER]:
        booking = await booking_crud.get_tenant_future_bookings(db, target_user.id)
        if booking:
            raise ValueError("User has future bookings, cannot delete")
    if target_user.role == UserRole.GUEST:
        booking = await booking_crud.get_bookings(
            db, guest_id=target_user.id, check_in=datetime.now(UTC).date(), active=True
        )
        if booking:
            raise ValueError("User has future bookings, cannot delete")
    success = await user_crud.soft_delete_user(db, target_user.id)
    if success:
        await db.commit()
    return success
