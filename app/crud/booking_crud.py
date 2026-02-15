from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import BookingStatus
from app.models import Booking


async def get_booking(db: AsyncSession, booking_id: UUID) -> Booking | None:
    """Get booking by ID."""
    return await db.get(Booking, booking_id)


async def get_bookings(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    guest_id: UUID | None = None,
    tenant_id: UUID | None = None,
    property_id: UUID | None = None,
    status: BookingStatus | None = None,
    check_in: date | None = None,
    check_out: date | None = None,
    active: bool | None = None,
) -> list[Booking]:
    """Get bookings with filters."""
    query = select(Booking).where(Booking.tenant_id == tenant_id)

    if guest_id:
        query = query.where(Booking.guest_id == guest_id)
    if property_id:
        query = query.where(Booking.property_id == property_id)
    if status:
        query = query.where(Booking.status == status)
    if check_in:
        query = query.where(Booking.check_in >= check_in)
    if check_out:
        query = query.where(Booking.check_out <= check_out)
    if active:
        query = query.where(
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        )

    query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_bookings_count(
    db: AsyncSession,
    guest_id: UUID | None = None,
    tenant_id: UUID | None = None,
    property_id: UUID | None = None,
    status: BookingStatus | None = None,
    check_in: date | None = None,
    check_out: date | None = None,
    active: bool | None = None,
) -> int:
    """Get total count of bookings."""
    query = select(func.count(Booking.id)).where(Booking.tenant_id == tenant_id)

    if guest_id:
        query = query.where(Booking.guest_id == guest_id)
    if property_id:
        query = query.where(Booking.property_id == property_id)
    if status:
        query = query.where(Booking.status == status)
    if check_in:
        query = query.where(Booking.check_in >= check_in)
    if check_out:
        query = query.where(Booking.check_out <= check_out)
    if active:
        query = query.where(
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        )

    result = await db.execute(query)
    return result.scalar_one()


async def check_availability(
    db: AsyncSession,
    property_id: UUID,
    check_in: date,
    check_out: date,
    exclude_booking_id: UUID | None = None,
) -> Booking | None:
    """
    Check if property is available for given dates.
    Returns conflicting booking if unavailable, None if available.
    Uses row-level locking to prevent race conditions.
    """
    from fastapi import HTTPException, status
    from sqlalchemy.exc import OperationalError

    query = (
        select(Booking)
        .where(
            Booking.property_id == property_id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.check_in < check_out,
            Booking.check_out > check_in,
        )
        .with_for_update(nowait=True)
    )

    if exclude_booking_id:
        query = query.where(Booking.id != exclude_booking_id)

    try:
        result = await db.execute(query)
        return result.scalars().first()
    except OperationalError:
        # Row is locked by another transaction (concurrent booking attempt)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Property is currently being booked by another user, please try again",
        )


async def create_booking(db: AsyncSession, booking_data: dict) -> Booking:
    """Create a new booking."""
    booking = Booking(**booking_data)
    db.add(booking)
    await db.flush()
    await db.refresh(booking)
    return booking


async def update_booking(
    db: AsyncSession, booking_id: UUID, **updates
) -> Booking | None:
    """Update booking fields."""
    booking = await db.get(Booking, booking_id)
    if not booking:
        return None

    for field, value in updates.items():
        if hasattr(booking, field):
            setattr(booking, field, value)

    await db.flush()
    await db.refresh(booking)
    return booking


async def get_expired_pending_bookings(db: AsyncSession) -> list[Booking]:
    """Get all pending bookings that have expired."""
    query = select(Booking).where(
        Booking.status == BookingStatus.PENDING,
        Booking.expires_at <= datetime.now(UTC),
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_future_bookings_by_tenant(
    db: AsyncSession, tenant_id: UUID
) -> list[Booking]:
    """Get all future bookings for a tenant."""
    query = select(Booking).where(
        Booking.tenant_id == tenant_id,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        Booking.check_in > datetime.now(UTC).date(),
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_tenant_future_bookings(db: AsyncSession, user_id: UUID) -> list[Booking]:
    """Get all bookings for a tenant."""
    query = select(Booking).where(
        Booking.manager_id == user_id, Booking.check_in > datetime.now(UTC).date()
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def check_property_availability(
    db: AsyncSession,
    property_id: UUID,
    check_in: date,
    check_out: date,
) -> Booking | None:
    """
    Check if property is available for given dates.
    Returns conflicting booking if unavailable, None if available.
    """

    query = select(Booking).where(
        Booking.property_id == property_id,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        Booking.check_in < check_out,
        Booking.check_out > check_in,
    )
    result = await db.execute(query)
    return result.scalars().first()
