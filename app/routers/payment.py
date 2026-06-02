import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.dependencies.types import DbDep, TenantUserDep
from app.schemas.payment import PaymentListResponse
from app.services import payment_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/callback/")
async def payment_callback(request: Request) -> RedirectResponse:
    """
    Handle Razorpay payment callback (redirect after payment).
    This endpoint receives the payment response and redirects to status page.
    """

    query_params = dict(request.query_params)
    token = query_params.get("token", "")
    booking_id = query_params.get("booking_id", "")
    payment_id = query_params.get("payment_id", "")

    redirect_url = (
        f"/static/html/payment-status.html"
        f"?token={token}"
        f"&booking_id={booking_id}"
        f"&payment_id={payment_id}"
    )

    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/webhook/")
async def webhook(request: Request, db: DbDep) -> dict:
    """
    Handle Razorpay webhook events.
    """

    # Starlette headers are case-insensitive.
    signature = request.headers.get("X-Razorpay-Signature")
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
        logger.info(f"Webhook event type: {payload.get('event')}")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON"
        )

    try:
        result = await payment_service.process_webhook(
            db, payload, body, signature, event_id
        )
        logger.info("Webhook processed successfully")
        return result
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise


@router.get("/booking/{booking_id}", response_model=PaymentListResponse)
async def get_booking_payments(
    booking_id: UUID,
    current_user: TenantUserDep,
    db: DbDep,
):
    payments = await payment_service.get_booking_payments(db, booking_id, current_user)
    if not payments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payments not found"
        )
    return {"total": len(payments), "data": payments}
