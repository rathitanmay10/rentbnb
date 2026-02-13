from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import message_crud
from app.database.init_db import get_db
from app.dependencies.user import get_current_user
from app.models import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageResponse
from app.services import message_service

router = APIRouter(prefix="/bookings", tags=["Messages"])


@router.get("/{booking_id}/messages", response_model=MessageListResponse)
async def get_messages(
    booking_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # TODO: Add auth check inside service or here
    # For now relying on message_service.create which checks auth
    # Read permission check:
    # We should probably add a checker in service or dependency
    messages = await message_crud.get_messages_by_booking(db, booking_id, skip, limit)
    total = await message_crud.get_messages_count(db, booking_id)
    return {"total": total, "data": messages}


@router.post("/{booking_id}/messages", response_model=MessageResponse)
async def send_message(
    booking_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await message_service.create_user_message(
        db, current_user, booking_id, message_data.content
    )
    # return await message_service.create_system_notification(
    #     db, booking_id, message_data.content, current_user.tenant_id
    # )
