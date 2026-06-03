import logging
from datetime import UTC, datetime

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, BackgroundTasks, Depends, status
from jose import JWTError, jwt

from app.constants.rate_limit import AUTH_LIMIT_SECONDS, AUTH_LIMIT_TIMES
from app.core.settings import settings
from app.dependencies.rate_limit import RateLimiter
from app.dependencies.types import CurrentUserDep, DbDep, TenantIdDep
from app.schemas.auth import (
    ChangePasswordSchema,
    EmailOnlySchema,
    ForgotPasswordSchema,
    LoginSchema,
    RefreshSchema,
    RegisterSchema,
    ResetPasswordSchema,
    TokenResponse,
    VerifyEmailSchema,
    VerifyLoginSchema,
)
from app.exceptions import BadRequestError
from app.schemas.error import BAD_REQUEST, FORBIDDEN, NOT_FOUND, TOO_MANY, UNAUTHORIZED
from app.schemas.response import MessageResponse
from app.services import auth_service

ALGO = settings.ALGORITHM
SECRET = settings.SECRET_KEY
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={**UNAUTHORIZED, **BAD_REQUEST},
)

# Rate limit applied to the public/credential endpoints only — not to
# refresh, change-password, or logout (which were never rate limited).
auth_rate_limit = Depends(
    RateLimiter(times=AUTH_LIMIT_TIMES, seconds=AUTH_LIMIT_SECONDS)
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
    summary="Register a new user",
    dependencies=[auth_rate_limit],
    responses={**FORBIDDEN, **TOO_MANY},
)
async def register(
    register_data: RegisterSchema,
    background_tasks: BackgroundTasks,
    db: DbDep,
    tenant_id: TenantIdDep,
) -> dict:
    """
    Register a new user (guest by default).

    - Sends verification email
    - User cannot login until email is verified
    """
    result = await auth_service.register_user(
        db, register_data, background_tasks, tenant_id
    )
    return result


@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Verify user email",
    dependencies=[auth_rate_limit],
    responses={**NOT_FOUND, **TOO_MANY},
)
async def verify_email(
    verify_data: VerifyEmailSchema,
    db: DbDep,
) -> dict:
    """
    Verify email using the token sent via email.
    """
    await auth_service.verify_email(db, verify_data.token)
    logger.info("Email verified successfully")
    return {"message": "Email verified successfully"}


@router.post(
    "/resend-verification-email",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Resend Verification Mail",
    dependencies=[auth_rate_limit],
    responses={**TOO_MANY},
)
async def resend_verify(
    resend_email: EmailOnlySchema,
    background_tasks: BackgroundTasks,
    db: DbDep,
    tenant_id: TenantIdDep,
) -> dict:
    """
    Resend Verification Email
    """
    result = await auth_service.resend_verification_email(
        db, resend_email, background_tasks, tenant_id
    )
    return result


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with Password",
    dependencies=[auth_rate_limit],
    responses={**FORBIDDEN, **NOT_FOUND, **TOO_MANY},
)
async def login_password(
    login_data: LoginSchema,
    db: DbDep,
    tenant_id: TenantIdDep,
) -> dict:
    """
    Standard login with email and password.
    """
    return await auth_service.login_password(db, login_data, tenant_id)


@router.post(
    "/login-otp",
    response_model=MessageResponse,
    summary="Login step 1: Send OTP (Passwordless)",
    dependencies=[auth_rate_limit],
    responses={**FORBIDDEN, **NOT_FOUND, **TOO_MANY},
)
async def login_otp_init(
    login_data: EmailOnlySchema,
    background_tasks: BackgroundTasks,
    db: DbDep,
    tenant_id: TenantIdDep,
) -> dict:
    """
    Initiate passwordless login. Sends OTP to email.
    """
    return await auth_service.login_otp_init(
        db, login_data.email, background_tasks, tenant_id
    )


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    summary="Login step 2: Verify OTP (Passwordless)",
    dependencies=[auth_rate_limit],
    responses={**FORBIDDEN, **NOT_FOUND, **TOO_MANY},
)
async def login_otp_verify(
    verify_data: VerifyLoginSchema,
    db: DbDep,
    tenant_id: TenantIdDep,
) -> dict:
    """
    Complete passwordless login by verifying OTP.
    """
    return await auth_service.login_otp_verify(db, verify_data, tenant_id)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh(
    refresh_data: RefreshSchema,
    db: DbDep,
) -> dict:
    """
    Refresh access token using refresh token.

    - Implements token rotation (old refresh token is blacklisted)
    - Issues new access and refresh token pair
    """
    result = await auth_service.refresh_tokens(db, refresh_data.refresh)
    return result


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Change password",
)
async def change_password(
    change_data: ChangePasswordSchema,
    current_user: CurrentUserDep,
    db: DbDep,
) -> dict:
    """
    Change user password.

    - Requires authentication
    - Validates old password
    - Invalidates all tokens (user must login again)
    """
    await auth_service.change_password(db, current_user, change_data)
    return {"message": "Password changed successfully. Please login again."}


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Request password reset",
    dependencies=[auth_rate_limit],
    responses={**NOT_FOUND, **TOO_MANY},
)
async def forgot_password(
    data: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    db: DbDep,
    tenant_id: TenantIdDep,
) -> dict:
    """
    Request password reset link.

    - Sends email with reset token if email exists
    """
    result = await auth_service.forgot_password(db, data, background_tasks, tenant_id)
    return result


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Reset password",
    dependencies=[auth_rate_limit],
    responses={**NOT_FOUND, **TOO_MANY},
)
async def reset_password(
    data: ResetPasswordSchema,
    db: DbDep,
    tenant_id: TenantIdDep,
) -> dict:
    """
    Reset password using token.

    - Changes password
    - Invalidates all existing sessions (token version increment)
    """
    result = await auth_service.reset_password(db, data, tenant_id)
    return result


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Logout user",
)
async def logout(
    refresh_data: RefreshSchema,
    current_user: CurrentUserDep,
    db: DbDep,
) -> dict:
    """
    Logout user by blacklisting refresh token.

    - Access token will expire naturally (15 min)
    - Refresh token is immediately blacklisted
    """
    try:
        payload = jwt.decode(
            refresh_data.refresh,
            SECRET,
            algorithms=[ALGO],
            options={"verify_exp": False},
        )
        jti = payload.get("jti")
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=UTC)
    except JWTError:
        raise BadRequestError("Invalid refresh token")

    await auth_service.logout(db, current_user, jti, expires_at)
    logger.info(f"User {current_user.id} logged out")
    return {"message": "Logged out successfully"}
