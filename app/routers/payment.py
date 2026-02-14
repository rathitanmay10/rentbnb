from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.crud import payment_crud
from app.database.init_db import get_db
from app.dependencies.user import get_current_user
from app.models import User
from app.schemas.payment import PaymentResponse
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/callback/")
async def payment_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Razorpay payment callback (redirect after payment).
    This endpoint receives the payment response and redirects to status page.
    """
    from fastapi.responses import RedirectResponse

    # Get form data from Razorpay
    form_data = await request.form()

    # Extract query parameters (token, booking_id, payment_id)
    query_params = dict(request.query_params)
    token = query_params.get("token", "")
    booking_id = query_params.get("booking_id", "")
    payment_id = query_params.get("payment_id", "")

    # Razorpay sends these fields
    razorpay_payment_id = form_data.get("razorpay_payment_id")
    razorpay_order_id = form_data.get("razorpay_order_id")
    razorpay_signature = form_data.get("razorpay_signature")

    # Build redirect URL with all parameters
    redirect_url = (
        f"/static/html/payment-status.html"
        f"?token={token}"
        f"&booking_id={booking_id}"
        f"&payment_id={payment_id}"
    )

    if razorpay_payment_id:
        redirect_url += f"&razorpay_payment_id={razorpay_payment_id}"
    if razorpay_order_id:
        redirect_url += f"&razorpay_order_id={razorpay_order_id}"
    if razorpay_signature:
        redirect_url += f"&razorpay_signature={razorpay_signature}"

    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/webhook/")
async def webhook(request: Request, db: AsyncSession = Depends(get_db)):
    import logging

    logger = logging.getLogger(__name__)

    # Log all headers for debugging
    logger.error(f"Webhook received. Headers: {dict(request.headers)}")

    # Check for signature in multiple header formats
    signature = (
        request.headers.get("X-Razorpay-Signature")
        or request.headers.get("x-razorpay-signature")
        or request.headers.get("X-RAZORPAY-SIGNATURE")
    )
    event_id = request.headers.get("x-razorpay-event-id")
    if not signature:
        logger.error(f"Missing signature. All headers: {dict(request.headers)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header"
        )
    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event id"
        )
    # Need raw body for verification
    body = await request.body()
    logger.error(f"Webhook body length: {len(body)} bytes")

    import hashlib
    import hmac

    logger.error(f"Body SHA256: {hashlib.sha256(body).hexdigest()}")
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    logger.error(f"Secret repr: {secret!r}")
    logger.error(f"Secret length: {len(secret)}")
    generated = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    logger.error(f"Generated signature: {generated}")
    logger.error(f"Received signature:  {signature}")
    logger.error(f"Signatures equal? {generated == signature}")
    try:
        payload = await request.json()
        logger.error(f"Webhook event type: {payload.get('event')}")
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
        )

    # Process webhook
    try:
        result = await payment_service.process_webhook(
            db, payload, body, signature, event_id
        )
        logger.info(f"Webhook processed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise


@router.get("/booking/{booking_id}", response_model=list[PaymentResponse])
async def get_booking_payments(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payments = await payment_crud.get_payments_by_booking(db, booking_id)
    return payments
