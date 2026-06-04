from uuid import UUID

from app.celery_app import celery_app
from app.services import booking_service
from app.tasks.base import db_async_task


@celery_app.task
@db_async_task
async def expire_pending_booking(db, booking_id: str):
    """Expire a pending booking if it hasn't been confirmed."""
    await booking_service.expire_booking(UUID(booking_id), db)


@celery_app.task
@db_async_task
async def sweep_expired_pending_bookings(db):
    """Periodic safety net: expire any pending bookings past their expiry."""
    await booking_service.sweep_expired_pending_bookings(db)
