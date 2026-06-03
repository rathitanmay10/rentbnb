import secrets
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.constants.auth_ttl import EMAIL_VERIFY_TTL
from app.constants.redis_keys import (
    REDIS_VERIFICATION_EMAIL,
    REDIS_VERIFICATION_TOKEN,
    get_tenant_prefix,
)
from app.dependencies.tenant import verify_tenant_access
from app.dependencies.types import (
    CurrentUserDep,
    DbDep,
    GuestUserDep,
    TenantOrSuperAdminDep,
)
from app.exceptions import TooManyRequestsError
from app.schemas import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserSelfUpdate,
    UserUpdate,
)
from app.schemas.error import (
    BAD_REQUEST,
    CONFLICT,
    FORBIDDEN,
    NOT_FOUND,
    TOO_MANY,
)
from app.services import email_service, user_service
from app.utils.email_utils import build_verification_email
from app.utils.redis_client import redis_client

router = APIRouter(
    prefix="/users", tags=["Users"], responses={**NOT_FOUND, **FORBIDDEN}
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    responses={**CONFLICT, **TOO_MANY, **BAD_REQUEST},
)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: DbDep,
    current_user: TenantOrSuperAdminDep,
):
    """
    Create a new user (TENANT_ADMIN or SUPER_ADMIN only).

    - TENANT_ADMIN can only create users in their own tenant
    - TENANT_ADMIN can only create MANAGER
    - SUPER_ADMIN can create users in any tenant
    - GUEST users will always have tenant_id=None
    - Email and username must be unique (case-insensitive)
    """
    user_service.authorize_user_creation(current_user, user_data)

    tenant_prefix = get_tenant_prefix(user_data.tenant_id)
    normalized_email = user_data.email.strip().lower()
    verification_key = (
        f"{tenant_prefix}{REDIS_VERIFICATION_EMAIL.format(email=normalized_email)}"
    )
    if await redis_client.get(verification_key) is not None:
        raise TooManyRequestsError("Verification email already sent. Please wait.")

    user = await user_service.create_user(db, user_data, user_data.tenant_id)

    token = secrets.token_urlsafe(32)
    await redis_client.set(
        f"{tenant_prefix}{REDIS_VERIFICATION_EMAIL.format(email=user.email)}",
        str(token),
        expire=EMAIL_VERIFY_TTL,
    )
    await redis_client.set(
        REDIS_VERIFICATION_TOKEN.format(token=token),
        str(user.id),
        expire=EMAIL_VERIFY_TTL,
    )

    email, subject, body = build_verification_email(token, user.email)
    background_tasks.add_task(
        email_service.email_service.send_email,
        to_email=email,
        subject=subject,
        body=body,
    )
    return user


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users",
)
async def list_users(
    db: DbDep,
    current_user: TenantOrSuperAdminDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List users with pagination.

    - SUPER_ADMIN sees all users
    - Other roles see only their tenant's users
    """
    users, total = await user_service.get_users(db, skip, limit, current_user)
    return {"total": total, "skip": skip, "limit": limit, "data": users}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: CurrentUserDep,
):
    """
    Get current authenticated user's profile.
    """
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: UUID,
    db: DbDep,
    current_user: TenantOrSuperAdminDep,
):
    """
    Get a specific user by ID.

    - SUPER_ADMIN can view any user
    - Other roles can only view users in their tenant
    """
    user = await user_service.get_user(db, user_id)
    if not user or user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify access
    verify_tenant_access(current_user, user)

    return user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    responses={**CONFLICT},
)
async def update_me(
    user_data: UserSelfUpdate,
    db: DbDep,
    current_user: CurrentUserDep,
):
    """
    Update current authenticated user's profile.
    """
    user = await user_service.update_user(db, current_user.id, user_data)
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    responses={**CONFLICT},
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: DbDep,
    current_user: TenantOrSuperAdminDep,
):
    """
    Update a user.
    """
    user = await user_service.update_user(db, user_id, user_data, current_user)
    return user


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Self delete user",
)
async def delete_me(
    db: DbDep,
    current_user: GuestUserDep,
) -> None:
    """
    Guest users can delete themselves
    """
    await user_service.delete_user(db, current_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete user",
    responses={**CONFLICT},
)
async def delete_user(
    user_id: UUID,
    db: DbDep,
    current_user: TenantOrSuperAdminDep,
) -> None:
    """
    Soft delete a user (TENANT_ADMIN or SUPER_ADMIN only).

    - TENANT_ADMIN can only delete users in their tenant
    - SUPER_ADMIN can delete any user
    - Data is not physically deleted, just marked as deleted
    """
    target_user = await user_service.get_user(db, user_id)
    if not target_user or target_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await user_service.delete_user(db, target_user, current_user)
