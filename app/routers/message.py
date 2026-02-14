from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.dependencies.tenant import get_tenant_user
from app.models import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageResponse
from app.services import message_service

router = APIRouter(prefix="/bookings", tags=["Messages"])


@router.get("/{booking_id}/messages", response_model=MessageListResponse)
async def get_messages(
    booking_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_tenant_user),
    db: AsyncSession = Depends(get_db),
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
    current_user: User = Depends(get_tenant_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message
    """
    return await message_service.create_user_message(
        db, current_user, booking_id, message_data.content
    )
