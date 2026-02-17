from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.jwt import TOKEN_TYPE_ACCESS
from app.core.settings import settings
from app.crud import booking_crud
from app.database.init_db import get_db
from app.enums import TenantStatus, UserRole
from app.models import User
from app.services import message_service
from app.utils.websocket_manager import manager

router = APIRouter(prefix="/ws", tags=["WebSocket"])


async def verify_websocket_token(token: str, db: AsyncSession) -> User | None:
    """
    Verify WebSocket token with full security checks.

    Validates:
    - Token format and signature
    - Token type (access)
    - Token version (for logout-all)
    - User exists and is active
    - Email is verified
    - User is not deleted
    - Tenant is active (tenant-aware)

    Returns:
        User object if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True},
        )
    except JWTError:
        return None

    if payload.get("type") != TOKEN_TYPE_ACCESS:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        user = await db.get(User, UUID(user_id))
    except ValueError:
        return None

    if not user or user.is_deleted:
        return None

    # Check token version (invalidates tokens after password change/logout-all)
    if payload.get("token_version") != user.token_version:
        return None

    if not user.is_active:
        return None

    if not user.is_verified:
        return None

    # Tenant-aware check: verify tenant is active
    if user.tenant_id and user.tenant:
        if user.tenant.is_deleted or user.tenant.status == TenantStatus.INACTIVE:
            return None

    return user


@router.websocket("/bookings/{booking_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    booking_id: UUID,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        await websocket.accept()

        # Validate token with robust security checks
        user = await verify_websocket_token(token, db)
        if not user:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid token or unauthorized",
            )
            return

        # Validate booking access
        booking = await booking_crud.get_booking(db, booking_id)
        if not booking:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason="Booking not found"
            )
            return

        is_guest = booking.guest_id == user.id
        is_manager = booking.property_manager_id == user.id
        is_tenant_admin = (
            user.role == UserRole.TENANT_ADMIN and user.tenant_id == booking.tenant_id
        )

        if not (is_guest or is_manager or is_tenant_admin):
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Access denied to this booking",
            )
            return

        # Connect
        await manager.connect(str(booking_id), websocket)

        try:
            while True:
                data = await websocket.receive_text()

                data = data.strip()
                if not data:
                    await websocket.send_json({"error": "Empty message"})
                    continue

                if len(data) > 2000:
                    await websocket.send_json({"error": "Message too long"})
                    continue

                await message_service.create_user_message(
                    db=db,
                    user=user,
                    booking_id=booking_id,
                    content=data,
                )

        except WebSocketDisconnect:
            manager.disconnect(str(booking_id), websocket)

    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
