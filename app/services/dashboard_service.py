import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import BookingStatus, PaymentStatus
from app.models import Booking, Payment, Tenant

logger = logging.getLogger(__name__)


async def get_tenant_dashboard(
    db: AsyncSession,
    tenant_id: UUID,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    """
    Get tenant dashboard metrics.
    """
    # Default date range: first day of current month to today
    if not from_date:
        from_date = datetime.now(UTC).date().replace(day=1)
    if not to_date:
        to_date = datetime.now(UTC).date()

    # Convert dates to datetime for comparison with created_at
    from_datetime = datetime.combine(from_date, datetime.min.time())
    to_datetime = datetime.combine(to_date, datetime.max.time())

    # 1. Total Revenue
    revenue_query = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.tenant_id == tenant_id,
        Payment.status == PaymentStatus.PAID,
        Payment.created_at >= from_datetime,
        Payment.created_at <= to_datetime,
    )
    revenue_result = await db.execute(revenue_query)
    total_revenue = revenue_result.scalar_one()

    # 2. Live Bookings (Active bookings within the date range)
    # Bookings where check_in <= to_date AND check_out > from_date
    live_bookings_query = select(func.count(Booking.id)).where(
        Booking.tenant_id == tenant_id,
        Booking.status == BookingStatus.CONFIRMED,
        Booking.check_in <= to_date,
        Booking.check_out > from_date,
    )
    live_bookings_result = await db.execute(live_bookings_query)
    live_bookings = live_bookings_result.scalar_one()

    # 3. Check-ins within the date range
    checkins_query = select(func.count(Booking.id)).where(
        Booking.tenant_id == tenant_id,
        Booking.status == BookingStatus.CONFIRMED,
        Booking.check_in >= from_date,
        Booking.check_in <= to_date,
    )
    checkins_result = await db.execute(checkins_query)
    total_checkins = checkins_result.scalar_one()

    # 4. Active Guests (Distinct guests with bookings in the date range)
    active_guests_query = select(func.count(func.distinct(Booking.guest_id))).where(
        Booking.tenant_id == tenant_id,
        Booking.status == BookingStatus.CONFIRMED,
        Booking.check_in <= to_date,
        Booking.check_out > from_date,
    )
    active_guests_result = await db.execute(active_guests_query)
    active_guests = active_guests_result.scalar_one()

    return {
        "total_revenue": Decimal(str(total_revenue)),
        "live_bookings": live_bookings,
        "active_checkins": total_checkins,
        "active_guests": active_guests,
    }


async def get_platform_dashboard(
    db: AsyncSession,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    """
    Get platform dashboard metrics.
    """
    # Default date range: first day of current month to today
    if not from_date:
        from_date = datetime.now(UTC).date().replace(day=1)
    if not to_date:
        to_date = datetime.now(UTC).date()

    # Convert dates to datetime for comparison
    from_datetime = datetime.combine(from_date, datetime.min.time())
    to_datetime = datetime.combine(to_date, datetime.max.time())

    # 1. Total Tenants
    total_tenants_query = select(func.count(Tenant.id)).where(
        Tenant.is_deleted.is_(False)
    )
    total_tenants_result = await db.execute(total_tenants_query)
    total_tenants = total_tenants_result.scalar_one()

    # 2. Total Platform Revenue (filtered by date range)
    revenue_query = select(func.coalesce(func.sum(Payment.amount), 0)).where(
        Payment.status == PaymentStatus.PAID,
        Payment.created_at >= from_datetime,
        Payment.created_at <= to_datetime,
    )
    revenue_result = await db.execute(revenue_query)
    total_revenue = revenue_result.scalar_one()

    # 3. Bookings within the date range
    bookings_query = select(func.count(Booking.id)).where(
        Booking.created_at >= from_datetime,
        Booking.created_at <= to_datetime,
    )
    bookings_result = await db.execute(bookings_query)
    bookings_in_range = bookings_result.scalar_one()

    return {
        "total_tenants": total_tenants,
        "total_revenue": Decimal(str(total_revenue)),
        "bookings_in_range": bookings_in_range,
    }
