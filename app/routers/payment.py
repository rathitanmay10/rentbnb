import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import payment_crud
from app.database.init_db import get_db
from app.dependencies.tenant import get_tenant_user
from app.models import User
from app.schemas.payment import PaymentListResponse
from app.services import payment_service

logger = logging.getLogger(__name__)
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

    form_data = await request.form()

    query_params = dict(request.query_params)
    token = query_params.get("token", "")
    booking_id = query_params.get("booking_id", "")
    payment_id = query_params.get("payment_id", "")

    razorpay_payment_id = form_data.get("razorpay_payment_id")
    razorpay_order_id = form_data.get("razorpay_order_id")
    razorpay_signature = form_data.get("razorpay_signature")
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
    """
    Handle Razorpay webhook events.
    """

    signature = (
        request.headers.get("X-Razorpay-Signature")
        or request.headers.get("x-razorpay-signature")
        or request.headers.get("X-RAZORPAY-SIGNATURE")
    )
    event_id = request.headers.get("x-razorpay-event-id")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header"
        )
    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing event id"
        )
    body = await request.body()

    try:
        payload = await request.json()
        logger.error(f"Webhook event type: {payload.get('event')}")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
        )

    try:
        result = await payment_service.process_webhook(
            db, payload, body, signature, event_id
        )
        logger.info(f"Webhook processed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise


@router.get("/booking/{booking_id}", response_model=PaymentListResponse)
async def get_booking_payments(
    booking_id: UUID,
    current_user: User = Depends(get_tenant_user),
    db: AsyncSession = Depends(get_db),
):

    payments = await payment_crud.get_payments_by_booking(
        db, booking_id, current_user.tenant_id
    )
    if not payments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payments not found"
        )
    return {"total": len(payments), "data": payments}
