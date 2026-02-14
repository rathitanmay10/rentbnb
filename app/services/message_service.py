from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, message_crud
from app.enums import MessageType, UserRole
from app.models import User
from app.utils.websocket_manager import manager


async def create_user_message(
    db: AsyncSession, user: User, booking_id: UUID, content: str
):
    """Create a message from a user."""
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    # Auth check
    is_guest = booking.guest_id == user.id
    is_manager = booking.property_manager_id == user.id
    is_tenant_admin = (
        user.role == UserRole.TENANT_ADMIN and user.tenant_id == booking.tenant_id
    )

    if not (is_guest or is_manager or is_tenant_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    message = await message_crud.create_message(
        db,
        {
            "booking_id": booking_id,
            "sender_id": user.id,
            "content": content,
            "message_type": MessageType.USER_MESSAGE,
            "tenant_id": booking.tenant_id,
        },
    )

    # Broadcast
    await manager.broadcast(
        str(booking_id),
        {
            "message": {
                "id": str(message.id),
                "content": message.content,
                "sender_id": str(message.sender_id),
                "created_at": message.created_at.isoformat(),
                "type": message.message_type,
            },
        },
    )

    return message


async def create_system_notification(
    db: AsyncSession, booking_id: UUID, content: str, tenant_id: UUID
):
    """Create a system notification."""
    message = await message_crud.create_message(
        db,
        {
            "booking_id": booking_id,
            "sender_id": None,
            "content": content,
            "message_type": MessageType.SYSTEM_NOTIFICATION,
            "tenant_id": tenant_id,
        },
    )

    # Broadcast
    await manager.broadcast(
        str(booking_id),
        {
            "message": {
                "id": str(message.id),
                "content": message.content,
                "sender_id": None,
                "created_at": message.created_at.isoformat(),
                "type": message.message_type,
            },
        },
    )

    return message


async def get_booking_messages(
    db: AsyncSession, user: User, booking_id: UUID, skip: int = 0, limit: int = 50
):
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    is_guest = booking.guest_id == user.id
    is_manager = booking.property_manager_id == user.id
    is_tenant_admin = (
        user.role == UserRole.TENANT_ADMIN and user.tenant_id == booking.tenant_id
    )
    if not (is_guest or is_manager or is_tenant_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    messages = await message_crud.get_messages_by_booking(db, booking_id, skip, limit)
    total = await message_crud.get_messages_count(db, booking_id)

    return messages, total
