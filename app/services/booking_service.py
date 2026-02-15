from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.constants.payment import COMMISSION_PERCENTAGE
from app.crud import booking_crud, payment_crud, property_crud, user_crud
from app.enums import BookingStatus, PaymentStatus, UserRole
from app.models import User
from app.schemas.booking import BookingCreate
from app.services import message_service, payment_service
from app.tasks.email_tasks import send_email_task
from app.utils.email_utils import build_booking_email


async def create_booking(
    db: AsyncSession,
    user: User,
    data: BookingCreate,
) -> dict:
    """Create a new booking and payment order."""

    # Lock the Property Row to serialize concurrent bookings for the SAME property.
    property_obj = await property_crud.get_property_with_lock(db, data.property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Check availability manually (since we have the lock, this is safe)
    # The lock ensures no one else is booking this property right now.
    conflict = await booking_crud.check_availability(
        db, data.property_id, data.check_in, data.check_out
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Property not available for selected dates",
        )

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
            "expires_at": datetime.now(UTC) + timedelta(minutes=10),
        },
    )
    await db.commit()
    await db.refresh(booking)

    # Create Razorpay order (External API Call - NO LOCK HELD)
    try:
        order = await payment_service.create_razorpay_order(
            db, booking.id, int(total_amount * 100)
        )
    except Exception as e:
        raise e

    # Create payment record
    payment = await payment_crud.create_payment(
        db,
        {
            "booking_id": booking.id,
            "guest_id": user.id,
            "tenant_id": property_obj.tenant_id,
            "status": PaymentStatus.PENDING,
            "amount": total_amount,
            "currency": "INR",
            "razorpay_order_id": order["id"],
        },
    )

    # Commit the transaction to persist payment
    await db.commit()

    # Schedule expiry task (Celery)
    from app.tasks.booking_tasks import expire_pending_booking

    expire_pending_booking.apply_async(args=[str(booking.id)], eta=booking.expires_at)

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    # Auth check: Guest or Manager or Admin
    is_guest = booking.guest_id == user.id
    is_manager = booking.property_manager_id == user.id
    is_admin = (
        user.role == UserRole.TENANT_ADMIN and user.tenant_id == booking.tenant_id
    )

    if not (is_guest or is_manager or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    if booking.status == BookingStatus.CANCELLED:
        return booking

    if booking.status == BookingStatus.CONFIRMED:
        days_to_checkin = (booking.check_in - datetime.now(UTC).date()).days
        if days_to_checkin >= 2:
            payments = await payment_crud.get_payments_by_booking(db, booking.id)
            for payment in payments:
                if payment.status == PaymentStatus.PAID:
                    from app.tasks.payment_tasks import refund_payment_task

                    refund_payment_task.delay(str(payment.id))

    await booking_crud.update_booking(
        db,
        booking.id,
        status=BookingStatus.CANCELLED,
        cancelled_at=datetime.now(UTC),
    )

    await db.commit()

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
            send_email_task.delay(email, subject, body)

    return booking


async def expire_booking(booking_id: UUID, db: AsyncSession):
    """Expire booking."""
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking:
        return

    if booking.status == BookingStatus.PENDING:
        await booking_crud.update_booking(
            db,
            booking.id,
            status=BookingStatus.CANCELLED,
            cancelled_at=datetime.now(UTC),
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
                send_email_task.delay(email, subject, body)
