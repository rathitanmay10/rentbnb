import secrets
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.auth_ttl import EMAIL_VERIFY_TTL
from app.crud import tenant_crud, user_crud
from app.enums import UserRole
from app.models import Tenant, User
from app.schemas import TenantCreate, TenantUpdate
from app.services.email_service import email_service
from app.utils.email_tasks import build_verification_email
from app.utils.password import hash_password
from app.utils.redis_client import redis_client


async def create_tenant(db: AsyncSession, tenant_data: TenantCreate) -> Tenant:
    """
    Create a new tenant with case-insensitive uniqueness check.
    """
    # Check for duplicate tenant name
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


async def create_tenant_with_admin(
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    company_name: str,
    admin_username: str,
    admin_email: str,
    admin_password: str,
) -> tuple[Tenant, "User"]:
    """
    Create tenant and admin user in a single transaction.
    Used for tenant registration flow.

    Returns:
        Tuple of (tenant, admin_user)

    Raises:
        ValueError: If tenant name, email, or username already exists
    """
    if await redis_client.get(f"verification:{admin_email}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Verification email already sent. Please wait.",
        )

    existing_tenant = await tenant_crud.get_tenant_by_name_ci(db, company_name.lower())
    if existing_tenant:
        raise ValueError("Tenant with this name already exists")

    existing_user_email = await user_crud.get_user_by_email_ci(db, admin_email.lower())
    if existing_user_email:
        raise ValueError("Email already in use")

    existing_user_username = await user_crud.get_user_by_username_ci(
        db, admin_username.lower()
    )
    if existing_user_username:
        raise ValueError("Username already in use")

    try:
        tenant = await tenant_crud.create_tenant(db, company_name)
        user_dict = {
            "username": admin_username.lower(),
            "email": admin_email.lower(),
            "hashed_password": hash_password(admin_password),
            "tenant_id": tenant.id,
            "role": UserRole.TENANT_ADMIN,
            "is_active": True,
            "is_verified": False,  # Requires email verification
        }
        admin_user = await user_crud.create_user(db, user_dict)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise e

    # Generate verification token
    token = secrets.token_urlsafe(32)

    # Store in Redis (24 hours)
    await redis_client.set(
        f"verification:{token}", str(admin_user.id), expire=EMAIL_VERIFY_TTL
    )
    await redis_client.set(
        f"verification:{admin_email}", str(token), expire=EMAIL_VERIFY_TTL
    )
    email, subject, body = build_verification_email(token, admin_user.email)
    background_tasks.add_task(email_service.send_email, email, subject, body)

    return tenant, admin_user


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
    Soft delete tenant and all associated users.

    Returns:
        True if successful, False if tenant not found
    """
    # Soft delete all users first
    await user_crud.soft_delete_users_by_tenant(db, tenant_id)

    # Then soft delete the tenant
    success = await tenant_crud.soft_delete_tenant(db, tenant_id)
    if success:
        await db.commit()
    return success
