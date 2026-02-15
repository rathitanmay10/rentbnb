from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.init_db import get_db
from app.dependencies import get_current_user
from app.dependencies.tenant import get_tenant_id_from_header
from app.models import User
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
from app.schemas.response import MessageResponse
from app.services import auth_service

ALGO = settings.ALGORITHM
SECRET = settings.SECRET_KEY
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
    summary="Register a new user",
)
async def register(
    register_data: RegisterSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
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
)
async def verify_email(
    verify_data: VerifyEmailSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email using the token sent via email.
    """
    await auth_service.verify_email(db, verify_data.token)
    return {"message": "Email verified successfully"}


@router.post(
    "/resend-verification-email",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Resend Verification Mail",
)
async def resend_verify(
    resend_email: EmailOnlySchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
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
)
async def login_password(
    login_data: LoginSchema,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
    """
    Standard login with email and password.
    """
    return await auth_service.login_password(db, login_data, tenant_id)


@router.post(
    "/login-otp",
    response_model=MessageResponse,
    summary="Login step 1: Send OTP (Passwordless)",
)
async def login_otp_init(
    login_data: EmailOnlySchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
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
)
async def login_otp_verify(
    verify_data: VerifyLoginSchema,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
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
    db: AsyncSession = Depends(get_db),
):
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
)
async def forgot_password(
    data: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
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
)
async def reset_password(
    data: ResetPasswordSchema,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
):
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token"
        )

    await auth_service.logout(db, current_user, jti)
    return {"message": "Logged out successfully"}
