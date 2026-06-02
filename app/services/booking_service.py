import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.booking import (
    BOOKING_EXPIRATION_MINUTES,
    CANCELLATION_REFUND_THRESHOLD_DAYS,
)
from app.constants.payment import COMMISSION_PERCENTAGE, DEFAULT_CURRENCY
from app.core.settings import settings
from app.crud import booking_crud, payment_crud, property_crud, user_crud
from app.enums import BookingStatus, PaymentStatus, UserRole
from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import User
from app.schemas.booking import BookingCreate
from app.services import message_service, payment_service
from app.tasks import booking_tasks, email_tasks, payment_tasks
from app.utils.email_utils import build_booking_email

logger = logging.getLogger(__name__)


async def create_booking(
    db: AsyncSession,
    user: User,
    data: BookingCreate,
) -> dict:
    """Create a new booking and payment order."""

    # Lock the Property Row to serialize concurrent bookings for the SAME property.
    property_obj = await property_crud.get_property_with_lock(
        db, data.property_id, user.tenant_id
    )
    if not property_obj:
        raise NotFoundError("Property not found")
    if not property_obj.is_active:
        raise ForbiddenError("Property is not active")
    # Check availability manually
    # The lock ensures no one else is booking this property right now.
    conflict = await booking_crud.check_availability(
        db, data.property_id, data.check_in, data.check_out
    )
    if conflict:
        raise ConflictError("Property not available for selected dates")

    nights = (data.check_out - data.check_in).days
    base_amount = nights * property_obj.price_per_night
    commission_amount = base_amount * (Decimal(str(COMMISSION_PERCENTAGE)) / 100)
    total_amount = base_amount + commission_amount
    # Create booking
    booking = await booking_crud.create_booking(
        db,
        {
            "property_id": data.property_id,
            "guest_id": user.id,
            "property_manager_id": property_obj.managed_by,
            "tenant_id": property_obj.tenant_id,
            "status": BookingStatus.PENDING,
            "check_in": data.check_in,
            "check_out": data.check_out,
            "base_amount": base_amount,
            "commission_amount": commission_amount,
            "total_amount": total_amount,
            "expires_at": datetime.now(UTC)
            + timedelta(minutes=BOOKING_EXPIRATION_MINUTES),
        },
    )
    await db.commit()
    await db.refresh(booking)

    # Create Razorpay order (External API Call - NO LOCK HELD)
    order = await payment_service.create_razorpay_order(
        db, booking.id, int(total_amount * 100)
    )

    # Create payment record
    payment = await payment_crud.create_payment(
        db,
        {
            "booking_id": booking.id,
            "guest_id": user.id,
            "tenant_id": property_obj.tenant_id,
            "status": PaymentStatus.PENDING,
            "amount": total_amount,
            "currency": DEFAULT_CURRENCY,
            "razorpay_order_id": order["id"],
        },
    )

    await db.commit()

    booking_tasks.expire_pending_booking.apply_async(
        args=[str(booking.id)], eta=booking.expires_at
    )

    return {
        "booking_id": booking.id,
        "payment_id": payment.id,
        "status": booking.status,
        "total_amount": total_amount,
        "expires_at": booking.expires_at,
        "razorpay_order_id": order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    }


async def cancel_booking(db: AsyncSession, booking_id: UUID, user: User):
    """Cancel booking."""
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking:
        raise NotFoundError("Booking not found")

    # Auth check: Guest or Manager or Admin
    is_guest = booking.guest_id == user.id
    is_manager = booking.property_manager_id == user.id
    is_admin = (
        user.role == UserRole.TENANT_ADMIN and user.tenant_id == booking.tenant_id
    )

    if not (is_guest or is_manager or is_admin):
        raise ForbiddenError("Not authorized")

    if booking.status == BookingStatus.CANCELLED:
        return booking

    if booking.status == BookingStatus.CONFIRMED:
        days_to_checkin = (booking.check_in - datetime.now(UTC).date()).days
        if days_to_checkin >= CANCELLATION_REFUND_THRESHOLD_DAYS:
            payments = await payment_crud.get_payments_by_booking(db, booking.id)
            for payment in payments:
                if payment.status == PaymentStatus.PAID:
                    payment_tasks.refund_payment_task.delay(str(payment.id))

    await booking_crud.update_booking(
        db,
        booking.id,
        status=BookingStatus.CANCELLED,
        cancelled_at=datetime.now(UTC),
    )

    await db.commit()

    logger.info(f"Booking {booking.id} cancelled by {user.id}")

    await message_service.create_system_notification(
        db, booking.id, "Booking cancelled.", booking.tenant_id
    )

    guest = await user_crud.get_user(db, booking.guest_id)
    if guest and guest.email:
        property_obj = await property_crud.get_property(db, booking.property_id)
        if property_obj:
            email, subject, body = build_booking_email(
                guest.email, booking, property_obj
            )
            email_tasks.send_email_task.delay(email, subject, body)

    return booking


async def list_bookings_for_user(
    db: AsyncSession,
    current_user: User,
    *,
    skip: int,
    limit: int,
    status: BookingStatus | None,
    property_id: UUID | None,
    check_in: date | None,
    check_out: date | None,
):
    """List bookings for the current user with role-based filtering."""
    guest_id = current_user.id if current_user.role == UserRole.GUEST else None
    property_manager_id = (
        current_user.id if current_user.role == UserRole.MANAGER else None
    )

    bookings = await booking_crud.get_bookings(
        db,
        skip=skip,
        limit=limit,
        guest_id=guest_id,
        property_manager_id=property_manager_id,
        tenant_id=current_user.tenant_id,
        status=status,
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
    )
    total = await booking_crud.get_bookings_count(
        db,
        guest_id=guest_id,
        property_manager_id=property_manager_id,
        tenant_id=current_user.tenant_id,
        status=status,
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
    )
    return bookings, total


async def get_booking_for_user(db: AsyncSession, booking_id: UUID, current_user: User):
    """Fetch a booking, enforcing tenant isolation and guest ownership."""
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking or booking.tenant_id != current_user.tenant_id:
        raise NotFoundError("Booking not found")
    if current_user.role == UserRole.GUEST and booking.guest_id != current_user.id:
        raise NotFoundError("Booking not found")
    return booking


async def expire_booking(booking_id: UUID, db: AsyncSession):
    """Expire booking."""
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking:
        return

    if booking.status == BookingStatus.PENDING:
        logger.info(f"Expiring pending booking: {booking.id}")
        await booking_crud.update_booking(
            db,
            booking.id,
            status=BookingStatus.FAILED,
        )

        await db.commit()

        await message_service.create_system_notification(
            db, booking.id, "Booking expired.", booking.tenant_id
        )

        guest = await user_crud.get_user(db, booking.guest_id)
        if guest and guest.email:
            property_obj = await property_crud.get_property(db, booking.property_id)
            if property_obj:
                email, subject, body = build_booking_email(
                    guest.email, booking, property_obj
                )
                email_tasks.send_email_task.delay(email, subject, body)
