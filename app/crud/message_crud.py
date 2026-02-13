from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message


async def get_messages_by_booking(
    db: AsyncSession, booking_id: UUID, skip: int = 0, limit: int = 50
) -> list[Message]:
    """Get messages for a booking."""
    query = (
        select(Message)
        .where(Message.booking_id == booking_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_messages_count(db: AsyncSession, booking_id: UUID) -> int:
    """Get total message count for a booking."""
    query = select(func.count(Message.id)).where(Message.booking_id == booking_id)
    result = await db.execute(query)
    return result.scalar_one()


async def create_message(db: AsyncSession, message_data: dict) -> Message:
    """Create a new message."""
    message = Message(**message_data)
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message
