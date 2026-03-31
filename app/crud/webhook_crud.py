from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Webhook


async def get_webhook_by_event_id(db: AsyncSession, event_id: str) -> Webhook | None:
    """Get webhook by Razorpay event ID."""
    query = select(Webhook).where(Webhook.razorpay_event_id == event_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_webhook(db: AsyncSession, webhook_data: dict) -> Webhook:
    """Create a new webhook record."""
    webhook = Webhook(**webhook_data)
    db.add(webhook)
    await db.flush()
    await db.refresh(webhook)
    return webhook


async def mark_webhook_processed(db: AsyncSession, webhook_id: UUID) -> None:
    """Mark webhook as processed."""
    webhook = await db.get(Webhook, webhook_id)
    if webhook:
        webhook.processed = True
        await db.flush()
