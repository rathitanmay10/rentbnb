from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import PaymentStatus
from app.models import Payment


async def get_payment(db: AsyncSession, payment_id: UUID) -> Payment | None:
    """Get payment by ID."""
    return await db.get(Payment, payment_id)


async def get_payment_by_order_id(db: AsyncSession, order_id: str) -> Payment | None:
    """Get payment by Razorpay order ID."""
    query = select(Payment).where(Payment.razorpay_order_id == order_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_payment_by_razorpay_payment_id(
    db: AsyncSession, payment_id: str
) -> Payment | None:
    """Get payment by Razorpay payment ID."""
    query = select(Payment).where(Payment.razorpay_payment_id == payment_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_payments_by_booking(
    db: AsyncSession, booking_id: UUID, tenant_id: UUID | None = None
) -> list[Payment]:
    """Get all payments for a booking."""
    query = select(Payment).where(Payment.booking_id == booking_id)
    if tenant_id:
        query = query.where(Payment.tenant_id == tenant_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_payment(db: AsyncSession, payment_data: dict) -> Payment:
    """Create a new payment."""
    payment = Payment(**payment_data)
    db.add(payment)
    await db.flush()
    await db.refresh(payment)
    return payment


async def update_payment(
    db: AsyncSession, payment_id: UUID, **updates
) -> Payment | None:
    """Update payment fields."""
    payment = await db.get(Payment, payment_id)
    if not payment:
        return None

    for field, value in updates.items():
        if hasattr(payment, field):
            setattr(payment, field, value)

    await db.flush()
    await db.refresh(payment)
    return payment


async def get_payments_to_poll(
    db: AsyncSession, time_windows: list[tuple[int, int]]
) -> list[Payment]:
    """
    Get pending payments that fall into specific age windows.
    time_windows: list of (min_age_minutes, max_age_minutes) tuples
    """
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import and_, or_

    now = datetime.now(UTC)
    conditions = []

    for min_age, max_age in time_windows:
        start_time = now - timedelta(minutes=max_age)
        end_time = now - timedelta(minutes=min_age)
        conditions.append(
            and_(Payment.created_at >= start_time, Payment.created_at <= end_time)
        )

    if not conditions:
        return []

    query = select(Payment).where(
        Payment.status == PaymentStatus.PENDING, or_(*conditions)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
