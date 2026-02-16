import secrets
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.auth_ttl import EMAIL_VERIFY_TTL
from app.database.init_db import get_db
from app.dependencies import get_current_user, require_tenant_or_super_admin
from app.dependencies.tenant import verify_tenant_access, verify_tenant_admin_management
from app.enums import UserRole
from app.models import User
from app.schemas import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services import email_service, user_service
from app.utils.email_utils import build_verification_email
from app.utils.redis_client import redis_client

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_tenant_or_super_admin),
):
    """
    Create a new user (TENANT_ADMIN or SUPER_ADMIN only).

    - TENANT_ADMIN can only create users in their own tenant
    - TENANT_ADMIN can only create MANAGER
    - SUPER_ADMIN can create users in any tenant
    - GUEST users will always have tenant_id=None
    - Email and username must be unique (case-insensitive)
    """

    if user_data.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admins cannot be created",
        )

    if current_user.role == UserRole.TENANT_ADMIN:
        if user_data.role not in [UserRole.MANAGER, UserRole.GUEST]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant admins can only create Managers or Guests",
            )
        tenant_id = current_user.tenant_id
        user_data.tenant_id = tenant_id
    tenant_prefix = f"tenant:{tenant_id}:"
    if (
        await redis_client.get(f"{tenant_prefix}verification:{user_data.email}")
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Verification email already sent. Please wait.",
        )

    try:
        user = await user_service.create_user(db, user_data, user_data.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = secrets.token_urlsafe(32)
    await redis_client.set(
        f"{tenant_prefix}verification:{user.email}", str(token), expire=EMAIL_VERIFY_TTL
    )
    await redis_client.set(
        f"verification:{token}", str(user.id), expire=EMAIL_VERIFY_TTL
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
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_tenant_or_super_admin),
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
    current_user: User = Depends(get_current_user),
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_tenant_or_super_admin),
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
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_tenant_or_super_admin),
):
    """
    Update a user.
    """
    target_user = await user_service.get_user(db, user_id)
    if not target_user or target_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check permissions

    if current_user.role == UserRole.TENANT_ADMIN:
        verify_tenant_admin_management(current_user, target_user)

    try:
        user = await user_service.update_user(db, user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_404_NOT_FOUND,
    summary="Soft delete user",
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_tenant_or_super_admin),
):
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

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot delete yourself"
        )
    if current_user.role == UserRole.TENANT_ADMIN:
        verify_tenant_admin_management(current_user, target_user)

    await user_service.delete_user(db, target_user)
    return
