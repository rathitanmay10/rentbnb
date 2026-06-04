from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, user_crud
from app.dependencies.tenant import verify_tenant_admin_management
from app.enums import UserRole
from app.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models import User
from app.schemas import UserCreate, UserSelfUpdate, UserUpdate
from app.utils.db_errors import extract_pg_error
from app.utils.password import hash_password


def authorize_user_creation(current_user: User, user_data: UserCreate) -> None:
    """
    Validate role/permission rules for creating a user and assign tenant_id
    for tenant admins.

    Raises:
        ForbiddenError: If a super admin is being created, or a tenant admin
            tries to create a disallowed role.
        BadRequestError: If a super admin does not provide a tenant_id.
    """
    if user_data.role == UserRole.SUPER_ADMIN:
        raise ForbiddenError("Super admins cannot be created")

    if current_user.role == UserRole.SUPER_ADMIN and user_data.tenant_id is None:
        raise BadRequestError("Super Admin needs to provide tenant_id")

    if current_user.role == UserRole.TENANT_ADMIN:
        if user_data.role not in [UserRole.MANAGER, UserRole.GUEST]:
            raise ForbiddenError("Tenant admins can only create Managers or Guests")
        user_data.tenant_id = current_user.tenant_id


async def create_user(
    db: AsyncSession, user_data: UserCreate, tenant_id: UUID | None = None
) -> User:
    """
    Create a new user with case-insensitive uniqueness checks.

    Raises:
        ConflictError: If email or username already exists.
    """
    # Check email uniqueness (case-insensitive) scoped to tenant
    existing_email = await user_crud.get_user_by_email_ci(
        db, user_data.email.lower(), tenant_id
    )
    if existing_email:
        raise ConflictError("Email already registered")

    # Check username uniqueness (case-insensitive) scoped to tenant
    existing_username = await user_crud.get_user_by_username_ci(
        db, user_data.username.lower(), tenant_id
    )
    if existing_username:
        raise ConflictError("Username already taken")

    user_dict = user_data.model_dump(exclude={"password"})
    user_dict["hashed_password"] = hash_password(user_data.password)

    user_dict["username"] = user_dict["username"].lower()
    user_dict["email"] = user_dict["email"].lower()

    try:
        user = await user_crud.create_user(db, user_dict)
        await db.commit()
        return user
    except IntegrityError as e:
        await db.rollback()
        error_msg = extract_pg_error(e).lower()
        if "email" in error_msg:
            raise ConflictError("Email already registered")
        if "username" in error_msg:
            raise ConflictError("Username already taken")
        raise


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
    db: AsyncSession,
    user_id: UUID,
    user_data: UserUpdate | UserSelfUpdate,
    current_user: User | None = None,
) -> User | None:
    """
    Update a user.

    When ``current_user`` is provided, the target user is loaded and
    permission/existence checks are enforced.

    Raises:
        NotFoundError: If the target user does not exist or is deleted.
    """
    if current_user is not None:
        target_user = await user_crud.get_user(db, user_id)
        if not target_user or target_user.is_deleted:
            raise NotFoundError("User not found")
        if current_user.role == UserRole.TENANT_ADMIN:
            try:
                verify_tenant_admin_management(current_user, target_user)
            except HTTPException as exc:
                raise ForbiddenError(exc.detail) from exc

    updates = user_data.model_dump(exclude_unset=True)

    try:
        user = await user_crud.update_user(db, user_id, **updates)
        if current_user is not None and not user:
            raise NotFoundError("User not found")
        await db.commit()
        return user
    except IntegrityError as e:
        await db.rollback()
        error_msg = extract_pg_error(e).lower()
        if "email" in error_msg:
            raise ConflictError("Email already registered")
        if "username" in error_msg:
            raise ConflictError("Username already taken")
        raise


async def delete_user(
    db: AsyncSession, target_user: User, current_user: User | None = None
) -> bool:
    """
    Soft delete a user.

    When ``current_user`` is provided, self-deletion and tenant-admin
    management permissions are enforced.

    Raises:
        ForbiddenError: If a user tries to delete themselves (when
            ``current_user`` is provided) or the target is a super admin.
        ConflictError: If the user has future bookings.
    """
    if current_user is not None:
        if target_user.id == current_user.id:
            raise ForbiddenError("You cannot delete yourself")
        if current_user.role == UserRole.TENANT_ADMIN:
            try:
                verify_tenant_admin_management(current_user, target_user)
            except HTTPException as exc:
                raise ForbiddenError(exc.detail) from exc

    if target_user.role == UserRole.SUPER_ADMIN:
        raise ForbiddenError("Super admin cannot be deleted")
    if target_user.role == UserRole.MANAGER:
        booking = await booking_crud.get_manager_future_bookings(db, target_user.id)
        if booking:
            raise ConflictError("User has future bookings, cannot delete")
    if target_user.role == UserRole.TENANT_ADMIN:
        booking = await booking_crud.get_future_bookings_by_tenant(
            db, target_user.tenant_id
        )
        if booking:
            raise ConflictError("User has future bookings, cannot delete")
    if target_user.role == UserRole.GUEST:
        booking = await booking_crud.get_bookings(
            db, guest_id=target_user.id, check_in=datetime.now(UTC).date(), active=True
        )
        if booking:
            raise ConflictError("User has future bookings, cannot delete")
    success = await user_crud.soft_delete_user(db, target_user.id)
    if success:
        await db.commit()
    return success
