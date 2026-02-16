import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.enums import PaymentStatus


class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    guest_id: uuid.UUID
    status: PaymentStatus
    amount: Decimal
    currency: str
    razorpay_order_id: str
    razorpay_payment_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    total: int
    data: list[PaymentResponse]


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class RazorpayWebhookPayload(BaseModel):
    """Razorpay webhook payload structure."""

    event: str
    payload: dict

    model_config = {"extra": "allow"}
