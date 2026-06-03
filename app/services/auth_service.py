import logging
import secrets
from datetime import UTC, datetime
from uuid import UUID

from fastapi import BackgroundTasks
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.auth_ttl import (
    EMAIL_VERIFY_TTL,
    RESEND_WAIT_SECONDS,
    RESET_PASSWORD_TTL,
)
from app.constants.jwt import TOKEN_TYPE_REFRESH
from app.constants.messages import (
    AUTH_INACTIVE,
    AUTH_INVALID_CREDENTIALS,
    AUTH_UNVERIFIED,
    OTP_SENT,
)
from app.constants.redis_keys import (
    REDIS_RESET_EMAIL,
    REDIS_RESET_TOKEN,
    REDIS_VERIFICATION_EMAIL,
    REDIS_VERIFICATION_TOKEN,
    get_tenant_prefix,
)
from app.core.settings import settings
from app.crud import blacklist_crud, user_crud
from app.enums import TenantStatus, UserRole
from app.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
)
from app.models import User
from app.schemas import UserCreate
from app.schemas.auth import (
    ChangePasswordSchema,
    EmailOnlySchema,
    ForgotPasswordSchema,
    LoginSchema,
    RegisterSchema,
    ResetPasswordSchema,
    VerifyLoginSchema,
)
from app.services import user_service
from app.services.email_service import email_service
from app.utils.email_utils import build_reset_password_email, build_verification_email
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.utils.otp_handler import OTPHandler
from app.utils.password import hash_password, verify_password
from app.utils.redis_client import redis_client

ALGO = settings.ALGORITHM
SECRET = settings.SECRET_KEY
logger = logging.getLogger(__name__)


async def register_user(
    db: AsyncSession,
    register_data: RegisterSchema,
    background_tasks: BackgroundTasks,
    tenant_id: UUID | None,
) -> dict:
    """
    Register a new user (guest by default) and send verification email.
    """
    # Scope redis key to tenant
    tenant_prefix = get_tenant_prefix(tenant_id)
    verification_key = (
        f"{tenant_prefix}{REDIS_VERIFICATION_EMAIL.format(email=register_data.email)}"
    )
    if await redis_client.get(verification_key) is not None:
        raise TooManyRequestsError("Verification email already sent. Please wait.")

    user_data = UserCreate(
        username=register_data.username,
        email=register_data.email,
        password=register_data.password,
        tenant_id=tenant_id,
        role=UserRole.GUEST,
    )

    user = await user_service.create_user(db, user_data, tenant_id)

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
        email_service.send_email, to_email=email, subject=subject, body=body
    )

    return {
        "message": "Registration successful. Please check your email to verify your account.",
    }


async def resend_verification_email(
    db: AsyncSession,
    data: EmailOnlySchema,
    background_tasks: BackgroundTasks,
    tenant_id: UUID | None,
):
    tenant_prefix = get_tenant_prefix(tenant_id)
    verification_key = (
        f"{tenant_prefix}{REDIS_VERIFICATION_EMAIL.format(email=data.email)}"
    )
    ttl = await redis_client.ttl(verification_key)
    if ttl > 0:
        elapsed = EMAIL_VERIFY_TTL - ttl
        if elapsed < RESEND_WAIT_SECONDS:
            raise TooManyRequestsError("Wait before resending.")
    user = await user_service.get_user_by_email(db, data.email, tenant_id)

    if not user:
        return {"message": "If email exists, a verification link has been sent."}

    if user.is_verified:
        return {"message": "User already verified."}

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
        email_service.send_email, to_email=email, subject=subject, body=body
    )
    return {
        "message": "Email sent, please check your email to verify your account.",
    }


async def verify_email(db: AsyncSession, token: str) -> bool:
    """Verify user email using token."""
    user_id = await redis_client.get(REDIS_VERIFICATION_TOKEN.format(token=token))

    if not user_id:
        raise BadRequestError("Invalid or expired verification token")

    user = await user_crud.get_user(db, UUID(user_id))
    if not user:
        raise NotFoundError("User not found")

    if user.is_verified:
        return True

    # Mark as verified
    await user_crud.update_user(db, user.id, is_verified=True, is_active=True)
    await db.commit()

    # Delete token
    await redis_client.delete(REDIS_VERIFICATION_TOKEN.format(token=token))

    # We need to delete the email rate limit key.
    # Since we don't have tenant_id here easily without fetching user (which we did),
    # we can construct the prefix.
    tenant_prefix = get_tenant_prefix(user.tenant_id)
    await redis_client.delete(
        f"{tenant_prefix}{REDIS_VERIFICATION_EMAIL.format(email=user.email)}"
    )

    return True


async def login_password(
    db: AsyncSession, login_data: LoginSchema, tenant_id: UUID | None
) -> dict:
    """
    Standard login with Email and Password.
    Returns Access and Refresh tokens.
    """
    user = await user_service.get_user_by_email(db, login_data.email, tenant_id)

    if not user:
        raise UnauthorizedError(AUTH_INVALID_CREDENTIALS)

    if not verify_password(login_data.password, user.hashed_password):
        raise UnauthorizedError(AUTH_INVALID_CREDENTIALS)

    if not user.is_active:
        raise ForbiddenError(AUTH_INACTIVE)

    if not user.is_verified:
        raise ForbiddenError(AUTH_UNVERIFIED)

    if user.tenant_id and user.tenant:
        if user.tenant.is_deleted or user.tenant.status == TenantStatus.INACTIVE:
            raise ForbiddenError("Tenant is inactive")

    # Issue tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    logger.info(f"User {user.id} logged in successfully (password)")

    return {"access": access_token, "refresh": refresh_token}


async def login_otp_init(
    db: AsyncSession,
    email: str,
    background_tasks: BackgroundTasks,
    tenant_id: UUID | None,
) -> dict:
    """
    Step 1 of Passwordless Login: Check user exists and send OTP.
    """
    user = await user_service.get_user_by_email(db, email, tenant_id)
    if not user:
        return {"message": OTP_SENT}

    if not user.is_active:
        raise ForbiddenError(AUTH_INACTIVE)
    await OTPHandler.send_otp(email, background_tasks, tenant_id)

    return {"message": OTP_SENT}


async def login_otp_verify(
    db: AsyncSession, verify_data: VerifyLoginSchema, tenant_id: UUID | None
) -> dict:
    """
    Step 2 of Passwordless Login: Verify OTP and issue tokens.
    """
    await OTPHandler.verify_otp(verify_data.email, verify_data.otp, tenant_id)

    user = await user_service.get_user_by_email(db, verify_data.email, tenant_id)
    if not user:
        raise NotFoundError("User not found")

    if not user.is_active:
        raise ForbiddenError(AUTH_INACTIVE)

    if user.tenant_id and user.tenant:
        if user.tenant.is_deleted or user.tenant.status == TenantStatus.INACTIVE:
            raise ForbiddenError("Tenant is inactive")

    # Issue tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    logger.info(f"User {user.id} logged in successfully (OTP)")

    return {"access": access_token, "refresh": refresh_token}


async def forgot_password(
    db: AsyncSession,
    data: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    tenant_id: UUID | None,
) -> dict:
    """Generate password reset token and send email."""
    tenant_prefix = get_tenant_prefix(tenant_id)
    reset_email_key = f"{tenant_prefix}{REDIS_RESET_EMAIL.format(email=data.email)}"
    ttl = await redis_client.ttl(reset_email_key)
    if ttl > 0:
        elapsed = RESET_PASSWORD_TTL - ttl
        if elapsed < RESEND_WAIT_SECONDS:
            raise TooManyRequestsError("Wait before resending.")
    user = await user_service.get_user_by_email(db, data.email, tenant_id)
    if not user:
        # Don't reveal user existence
        return {"message": "If email exists, a reset link has been sent"}

    token = secrets.token_urlsafe(32)
    await redis_client.set(
        f"{tenant_prefix}{REDIS_RESET_EMAIL.format(email=data.email)}",
        str(user.id),
        expire=RESET_PASSWORD_TTL,
    )
    await redis_client.set(
        f"{tenant_prefix}{REDIS_RESET_TOKEN.format(token=token)}",
        str(user.id),
        expire=RESET_PASSWORD_TTL,
    )

    email, subject, body = build_reset_password_email(token, user.email)
    background_tasks.add_task(
        email_service.send_email, to_email=email, subject=subject, body=body
    )

    return {"message": "If email exists, a reset link has been sent"}


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
    """
    Refresh access token using refresh token.
    """
    try:
        payload = jwt.decode(refresh_token, SECRET, algorithms=[ALGO])
    except JWTError:
        raise UnauthorizedError("Invalid refresh token")

    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    jti = payload.get("jti")

    # Check if token is blacklisted
    if await blacklist_crud.is_token_blacklisted(db, jti):
        raise UnauthorizedError("Token has been revoked")

    user = await user_crud.get_user(db, UUID(user_id))
    if not user:
        raise UnauthorizedError("User not found")

    # Check token version
    if payload.get("token_version") != user.token_version:
        raise UnauthorizedError("Token has been invalidated")

    # Issue new pair
    access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)

    # Blacklist old refresh token
    expires_at = datetime.fromtimestamp(payload.get("exp"), tz=UTC)
    await blacklist_crud.blacklist_token(db, user.id, jti, expires_at)
    await db.commit()

    return {"access": access_token, "refresh": new_refresh_token}


async def change_password(
    db: AsyncSession, user: User, change_data: ChangePasswordSchema
) -> bool:
    """
    Change user password and invalidate all tokens.
    """
    # Verify old password
    if not verify_password(change_data.old_password, user.hashed_password):
        raise BadRequestError("Incorrect old password")

    # Update password
    new_hashed = hash_password(change_data.new_password)
    await user_crud.update_user(db, user.id, hashed_password=new_hashed)

    # Increment token version (invalidates all tokens)
    await user_crud.increment_token_version(db, user.id)
    await db.commit()

    return True


async def logout(
    db: AsyncSession, user: User, refresh_token_jti: str, expires_at: datetime
) -> bool:
    """
    Logout user by blacklisting their refresh token.
    """
    await blacklist_crud.blacklist_token(db, user.id, refresh_token_jti, expires_at)
    await db.commit()

    return True


async def reset_password(
    db: AsyncSession, data: ResetPasswordSchema, tenant_id: UUID | None
) -> dict:
    """Reset password using token."""
    tenant_prefix = get_tenant_prefix(tenant_id)
    reset_token_key = f"{tenant_prefix}{REDIS_RESET_TOKEN.format(token=data.token)}"
    user_id = await redis_client.get(reset_token_key)
    if not user_id:
        raise BadRequestError("Invalid or expired reset token")

    user = await user_crud.get_user(db, UUID(user_id))
    if not user:
        raise NotFoundError("User not found")

    # Update password
    new_hashed = hash_password(data.new_password)
    await user_crud.update_user(db, user.id, hashed_password=new_hashed)

    # Invalidate old sessions
    await user_crud.increment_token_version(db, user.id)
    await db.commit()

    # Delete token
    await redis_client.delete(
        f"{tenant_prefix}{REDIS_RESET_TOKEN.format(token=data.token)}"
    )
    await redis_client.delete(
        f"{tenant_prefix}{REDIS_RESET_EMAIL.format(email=user.email)}"
    )

    return {"message": "Password reset successful"}
