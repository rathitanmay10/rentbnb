from uuid import UUID

from fastapi import APIRouter, Query

from app.dependencies.types import DbDep, TenantUserDep
from app.schemas.error import (
    FORBIDDEN,
    NOT_FOUND,
)
from app.schemas.message import MessageCreate, MessageListResponse, MessageResponse
from app.services import message_service

router = APIRouter(
    prefix="/bookings", tags=["Messages"], responses={**NOT_FOUND, **FORBIDDEN}
)


@router.get("/{booking_id}/messages", response_model=MessageListResponse)
async def get_messages(
    booking_id: UUID,
    current_user: TenantUserDep,
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get all messages for a booking
    """
    messages, total = await message_service.get_booking_messages(
        db, current_user, booking_id, skip, limit
    )
    return {"total": total, "skip": skip, "limit": limit, "data": messages}


@router.post("/{booking_id}/messages", response_model=MessageResponse)
async def send_message(
    booking_id: UUID,
    message_data: MessageCreate,
    current_user: TenantUserDep,
    db: DbDep,
):
    """
    Send a message
    """
    return await message_service.create_user_message(
        db, current_user, booking_id, message_data.content
    )
