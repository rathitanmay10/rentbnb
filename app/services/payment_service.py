import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud import booking_crud, payment_crud, property_crud, user_crud, webhook_crud
from app.enums import BookingStatus, PaymentStatus
from app.services import message_service
from app.tasks.email_tasks import send_email_task
from app.utils.email_utils import build_booking_email
from app.utils.razorpay_client import RazorpayClient

logger = logging.getLogger(__name__)


async def create_razorpay_order(
    db: AsyncSession, booking_id: UUID, amount: float, currency: str = "INR"
) -> dict:
    """Create Razorpay order."""
    # Amount needed in paise
    amount_paise = int(amount * 100)

    data = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": str(booking_id),
        "notes": {"booking_id": str(booking_id)},
    }

    try:
        order = await RazorpayClient.create_order(data=data)
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Razorpay order creation failed: {e!s}",
        )


async def verify_payment_signature(
    razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str
) -> bool:
    """Verify payment signature from client."""
    try:
        RazorpayClient.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )
        return True
    except Exception:
        return False


async def process_webhook(
    db: AsyncSession, payload: dict, body: bytes, signature: str, event_id: str
):
    """Process Razorpay webhook."""
    # 1. Verify signature
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    logger.info(
        f"Webhook secret configured: {settings.RAZORPAY_WEBHOOK_SECRET[:10]}..."
    )
    logger.info(f"Received signature: {signature[:20]}...")
    logger.info(f"Body type: {type(body)}, length: {len(body)}")

    try:
        client = RazorpayClient.get_client()
        # Razorpay expects body as string, not bytes
        body_str = body.decode("utf-8")
        logger.info(f"Verifying signature with body string length: {len(body_str)}")

        client.utility.verify_webhook_signature(
            body_str, signature, settings.RAZORPAY_WEBHOOK_SECRET
        )
        logger.info("Webhook signature verified successfully")
    except Exception as e:
        logger.error(f"Signature verification failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    event_id = event_id
    event_type = payload.get("event")

    # 2. Deduplication & Idempotency
    webhook = await webhook_crud.get_webhook_by_event_id(db, event_id)

    if webhook:
        if webhook.processed:
            return {"status": "ignored", "reason": "already_processed"}
        # If exists but not processed, we continue to processing
        logger.info(f"Retrying processing for existing webhook {event_id}")
    else:
        # 3. Store webhook
        webhook = await webhook_crud.create_webhook(
            db,
            {
                "event_type": event_type,
                "payload": payload,
                "razorpay_event_id": event_id,
                "processed": False,
                "tenant_id": None,
            },
        )
        # We commit here to ensure we have the record
        await db.commit()

    # 4. Process event
    try:
        if event_type == "payment.captured":
            await _handle_payment_captured(db, payload)
        elif event_type == "payment.failed":
            await _handle_payment_failed(db, payload)
        elif event_type == "refund.processed":
            await _handle_refund_processed(db, payload)
        elif event_type == "refund.created":
            logger.info(f"Refund created for event {event_id}")
        elif event_type == "refund.failed":
            logger.error(f"Refund failed for event {event_id}")

        await webhook_crud.mark_webhook_processed(db, webhook.id)
        await db.commit()
    except Exception as e:
        # Log error, webhook remains unprocessed
        raise e

    return {"status": "processed"}


async def _handle_payment_captured(db: AsyncSession, payload: dict):
    payment_entity = payload["payload"]["payment"]["entity"]
    order_id = payment_entity["order_id"]
    payment_id = payment_entity["id"]
    amount = payment_entity["amount"] / 100  # Convert back to main unit

    payment = await payment_crud.get_payment_by_order_id(db, order_id)
    if not payment:
        return  # Should not happen if flow is correct

    booking = await booking_crud.get_booking(db, payment.booking_id)
    if not booking:
        return

    # Amount mismatch check
    if float(payment.amount) != float(amount):
        # Mark payment failed
        await payment_crud.update_payment(
            db, payment.id, status=PaymentStatus.FAILED, razorpay_payment_id=payment_id
        )
        # Attempt refund
        await process_refund(db, payment.id)

        await message_service.create_system_notification(
            db, booking.id, "Payment failed: Amount mismatch", booking.tenant_id
        )

        guest = await user_crud.get_user(db, booking.guest_id)
        if guest and guest.email:
            property_obj = await property_crud.get_property(db, booking.property_id)
            if property_obj:
                email, subject, body = build_booking_email(
                    guest.email, booking, property_obj
                )
                # Override subject for failure
                subject = "Payment Failed: Amount Mismatch"
                body = f"Your payment for booking {booking.id} failed due to amount mismatch. Refund initiated."
                send_email_task.delay(email, subject, body)
        return

    # Update payment
    await payment_crud.update_payment(
        db, payment.id, status=PaymentStatus.PAID, razorpay_payment_id=payment_id
    )

    # Update booking
    if booking.status == BookingStatus.PENDING:
        await booking_crud.update_booking(
            db, booking.id, status=BookingStatus.CONFIRMED
        )
        await message_service.create_system_notification(
            db, booking.id, "Booking confirmed! Payment successful.", booking.tenant_id
        )
        guest = await user_crud.get_user(db, booking.guest_id)
        if guest and guest.email:
            property_obj = await property_crud.get_property(db, booking.property_id)
            if property_obj:
                email, subject, body = build_booking_email(
                    guest.email, booking, property_obj
                )
                send_email_task.delay(email, subject, body)

    elif booking.status == BookingStatus.CANCELLED:
        # Late payment - Booking already cancelled/expired
        logger.info(
            f"Payment captured for cancelled booking {booking.id}. Initiating refund."
        )
        await process_refund(db, payment.id)

    await db.commit()
    # Payment status will be updated to REFUNDED by process_refund if successful


async def _handle_payment_failed(db: AsyncSession, payload: dict):
    payment_entity = payload["payload"]["payment"]["entity"]
    order_id = payment_entity["order_id"]

    payment = await payment_crud.get_payment_by_order_id(db, order_id)
    if payment:
        await payment_crud.update_payment(db, payment.id, status=PaymentStatus.FAILED)

        # Send email
        # Ideally we should also get booking to notify user
        # Payment -> Booking
        booking = await booking_crud.get_booking(db, payment.booking_id)
        if booking:
            from app.crud import user_crud
            from app.tasks.email_tasks import send_email_task
            from app.utils.email_utils import build_booking_email

            guest = await user_crud.get_user(db, booking.guest_id)
            if guest and guest.email:
                property_obj = await property_crud.get_property(db, booking.property_id)
                if property_obj:
                    email, subject, body = build_booking_email(
                        guest.email, booking, property_obj
                    )
                    subject = "Payment Failed"
                    body = f"Your payment for booking {booking.id} has failed."
                    send_email_task.delay(email, subject, body)

    await db.commit()


async def process_refund(db: AsyncSession, payment_id: UUID):
    payment = await payment_crud.get_payment(db, payment_id)
    if not payment:
        return

    if payment.status == PaymentStatus.REFUNDED:
        return

    try:
        await RazorpayClient.refund_payment(
            payment.razorpay_payment_id, {"amount": int(payment.amount * 100)}
        )
        await payment_crud.update_payment(db, payment.id, status=PaymentStatus.REFUNDED)
    except Exception as e:
        logger.error(f"Refund failed for payment {payment.id}: {e}")


async def _handle_refund_processed(db: AsyncSession, payload: dict):
    payload_data = payload.get("payload", {})
    refund_entity = payload_data.get("refund", {}).get("entity", {})
    payment_id = refund_entity.get("payment_id")

    payment = await payment_crud.get_payment_by_razorpay_payment_id(db, payment_id)
    if payment:
        await payment_crud.update_payment(db, payment.id, status=PaymentStatus.REFUNDED)
        logger.info(f"Payment {payment.id} marked as REFUNDED via webhook")
    else:
        logger.warning(f"Received refund.processed for unknown payment {payment_id}")


async def check_payment_status(db: AsyncSession, payment_id: UUID):
    """Check payment status via Razorpay API (Polling)."""
    payment = await payment_crud.get_payment(db, payment_id)
    if not payment:
        return

    if payment.status != PaymentStatus.PENDING:
        return

    try:
        # poll for payments associated with order
        response = await RazorpayClient.fetch_order_payments(payment.razorpay_order_id)
        items = response.get("items", [])

        for item in items:
            if item["status"] == "captured":
                # Verify amount
                amount_paid = item["amount"] / 100
                if amount_paid == float(payment.amount):
                    # Success
                    await payment_crud.update_payment(
                        db,
                        payment.id,
                        status=PaymentStatus.PAID,
                        razorpay_payment_id=item["id"],
                    )

                    # Update booking
                    booking = await booking_crud.get_booking(db, payment.booking_id)
                    if not booking:
                        return

                    if booking.status == BookingStatus.PENDING:
                        await booking_crud.update_booking(
                            db, booking.id, status=BookingStatus.CONFIRMED
                        )
                        await message_service.create_system_notification(
                            db,
                            booking.id,
                            "Booking confirmed via payment verification.",
                            booking.tenant_id,
                        )

                        # Send email
                        from app.crud import user_crud
                        from app.tasks.email_tasks import send_email_task
                        from app.utils.email_utils import build_booking_email

                        guest = await user_crud.get_user(db, booking.guest_id)
                        if guest and guest.email:
                            property_obj = await property_crud.get_property(
                                db, booking.property_id
                            )
                            if property_obj:
                                email, subject, body = build_booking_email(
                                    guest.email, booking, property_obj
                                )
                                send_email_task.delay(email, subject, body)

                    elif booking.status == BookingStatus.CANCELLED:
                        # Late payment detected via polling
                        logger.info(
                            f"Polling detected payment for cancelled booking {booking.id}. Initiating refund."
                        )
                        await process_refund(db, payment.id)

                    return
    except Exception as e:
        logger.error(f"Polling check failed for payment {payment_id}: {e}")
        raise e
