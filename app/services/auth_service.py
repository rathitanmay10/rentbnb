import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import BackgroundTasks, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.constants.auth_ttl import (
    EMAIL_VERIFY_TTL,
    RESEND_WAIT_SECONDS,
    RESET_PASSWORD_TTL,
)
from app.constants.messages import (
    AUTH_INACTIVE,
    AUTH_INVALID_CREDENTIALS,
    AUTH_UNVERIFIED,
    OTP_SENT,
)
from app.crud import blacklist_crud, user_crud
from app.enums import TenantStatus, UserRole
from app.models import User
from app.schemas.auth import (
    ChangePasswordSchema,
    EmailOnlySchema,
    ForgotPasswordSchema,
    LoginSchema,
    RegisterSchema,
    ResetPasswordSchema,
    VerifyLoginSchema,
)
from app.services import email_service, user_service
from app.utils.email_tasks import build_verification_email
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.utils.otp_handler import OTPHandler
from app.utils.password import hash_password, verify_password
from app.utils.redis_client import redis_client

ALGO = settings.ALGORITHM
SECRET = settings.SECRET_KEY


async def register_user(
    db: AsyncSession, register_data: RegisterSchema, background_tasks: BackgroundTasks
) -> dict:
    """
    Register a new user (guest by default) and send verification email.
    """
    if await redis_client.get(f"verification:{register_data.email}") is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Verification email already sent. Please wait.",
        )

    from app.schemas import UserCreate

    user_data = UserCreate(
        username=register_data.username,
        email=register_data.email,
        password=register_data.password,
        tenant_id=None,
        role=UserRole.GUEST,
    )

    try:
        user = await user_service.create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = secrets.token_urlsafe(32)
    await redis_client.set(
        f"verification:{user.email}", str(token), expire=EMAIL_VERIFY_TTL
    )
    await redis_client.set(
        f"verification:{token}", str(user.id), expire=EMAIL_VERIFY_TTL
    )

    email, subject, body = build_verification_email(token, user.email)
    background_tasks.add_task(
        email_service.email_service.send_email, email, subject, body
    )

    return {
        "message": "Registration successful. Please check your email to verify your account.",
    }


async def verify_email(db: AsyncSession, token: str) -> bool:
    """Verify user email using token."""
    user_id = await redis_client.get(f"verification:{token}")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user = await user_crud.get_user(db, UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_verified:
        return True

    # Mark as verified
    await user_crud.update_user(db, user.id, is_verified=True, is_active=True)
    await db.commit()

    # Delete token
    await redis_client.delete(f"verification:{token}")
    await redis_client.delete(f"verification:{user.email}")

    return True


async def resend_verfication_email(
    db: AsyncSession, data: EmailOnlySchema, background_tasks: BackgroundTasks
):
    ttl = await redis_client.ttl(f"verification:{data.email}")
    if ttl > 0:
        elapsed = EMAIL_VERIFY_TTL - ttl
        if elapsed < RESEND_WAIT_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Wait before resending.",
            )
    user = await user_service.get_user_by_email(db, data.email)

    if not user:
        return {"message": "If email exists, a verification link has been sent."}

    if user.is_verified:
        return {"message": "User already verified."}

    token = secrets.token_urlsafe(32)
    await redis_client.set(
        f"verification:{user.email}", str(token), expire=EMAIL_VERIFY_TTL
    )
    await redis_client.set(
        f"verification:{token}", str(user.id), expire=EMAIL_VERIFY_TTL
    )

    email, subject, body = build_verification_email(token, user.email)
    background_tasks.add_task(
        email_service.email_service.send_email, email, subject, body
    )
    return {
        "message": "Email sent, please check your email to verify your account.",
    }


async def login_password(db: AsyncSession, login_data: LoginSchema) -> dict:
    """
    Standard login with Email and Password.
    Returns Access and Refresh tokens.
    """
    user = await user_service.get_user_by_email(db, login_data.email)

    if not user:
        # Avoid user enumeration (marketing/timing attack mitigation)
        # In a real app we might want to standardize timing here
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_INVALID_CREDENTIALS
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=AUTH_INVALID_CREDENTIALS
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_INACTIVE)

    # Check if email is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=AUTH_UNVERIFIED,
        )

    # Check if tenant is active (if user has a tenant)
    if user.tenant_id and user.tenant:
        if user.tenant.is_deleted or user.tenant.status == TenantStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive"
            )

    # Issue tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return {"access": access_token, "refresh": refresh_token}


async def login_otp_init(
    db: AsyncSession, email: str, background_tasks: BackgroundTasks
) -> dict:
    """
    Step 1 of Passwordless Login: Check user exists and send OTP.
    """
    user = await user_service.get_user_by_email(db, email)
    if not user:
        # Return success to avoid user enumeration
        return {"message": OTP_SENT}

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_INACTIVE)

    # Send OTP using OTPHandler
    await OTPHandler.send_otp(email, background_tasks)

    return {"message": OTP_SENT}


async def login_otp_verify(db: AsyncSession, verify_data: VerifyLoginSchema) -> dict:
    """
    Step 2 of Passwordless Login: Verify OTP and issue tokens.
    """
    # Verify OTP
    await OTPHandler.verify_otp(verify_data.email, verify_data.otp)

    # Get user
    user = await user_service.get_user_by_email(db, verify_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=AUTH_INACTIVE)

    # Issue tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)

    return {"access": access_token, "refresh": refresh_token}


async def forgot_password(
    db: AsyncSession, data: ForgotPasswordSchema, background_tasks: BackgroundTasks
) -> dict:
    """Generate password reset token and send email."""
    user = await user_service.get_user_by_email(db, data.email)
    if not user:
        # Don't reveal user existence
        return {"message": "If email exists, a reset link has been sent"}

    token = secrets.token_urlsafe(32)

    await redis_client.set(f"reset:{token}", str(user.id), expire=RESET_PASSWORD_TTL)

    subject = "Reset Password"
    body = f"Please reset your password by clicking this link {settings.FRONTEND_URL}/reset-password?token={token}"
    background_tasks.add_task(
        email_service.email_service.send_email, user.email, subject, body
    )

    return {"message": "If email exists, a reset link has been sent"}


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
    """
    Refresh access token using refresh token.
    """
    try:
        payload = jwt.decode(refresh_token, SECRET, algorithms=[ALGO])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    user_id = payload.get("sub")
    jti = payload.get("jti")

    # Check if token is blacklisted
    if await blacklist_crud.is_token_blacklisted(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
        )

    user = await user_crud.get_user(db, UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    # Check token version
    if payload.get("token_version") != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
        )

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password"
        )

    # Update password
    new_hashed = hash_password(change_data.new_password)
    await user_crud.update_user(db, user.id, hashed_password=new_hashed)

    # Increment token version (invalidates all tokens)
    await user_crud.increment_token_version(db, user.id)
    await db.commit()

    return True


async def logout(db: AsyncSession, user: User, refresh_token_jti: str) -> bool:
    """
    Logout user by blacklisting their refresh token.
    """
    # For now, set a far future date (tokens will be cleaned up periodically)
    expires_at = datetime.now(UTC) + timedelta(days=30)

    await blacklist_crud.blacklist_token(db, user.id, refresh_token_jti, expires_at)
    await db.commit()

    return True


async def reset_password(db: AsyncSession, data: ResetPasswordSchema) -> dict:
    """Reset password using token."""
    user_id = await redis_client.get(f"reset:{data.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = await user_crud.get_user(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password
    new_hashed = hash_password(data.new_password)
    await user_crud.update_user(db, user.id, hashed_password=new_hashed)

    # Invalidate old sessions
    await user_crud.increment_token_version(db, user.id)
    await db.commit()

    # Delete token
    await redis_client.delete(f"reset:{data.token}")

    return {"message": "Password reset successful"}
