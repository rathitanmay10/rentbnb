import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.constants.booking import MAX_ADVANCE_BOOKING_DAYS, MAX_BOOKING_DURATION_DAYS
from app.enums import BookingStatus
from app.schemas.payment import PaymentResponse


class BookingBase(BaseModel):
    property_id: uuid.UUID
    check_in: date
    check_out: date


class BookingCreate(BookingBase):
    @field_validator("check_in")
    @classmethod
    def check_in_future(cls, v: date) -> date:
        if v <= datetime.now(UTC).date():
            raise ValueError("Check-in must be in the future")
        return v

    @field_validator("check_out")
    @classmethod
    def check_out_after_check_in(cls, v: date, info) -> date:
        if "check_in" in info.data and v <= info.data["check_in"]:
            raise ValueError("Check-out must be after check-in")
        return v

    @model_validator(mode="after")
    def validate_booking_constraints(self):
        # Max booking duration
        duration = (self.check_out - self.check_in).days
        if duration > MAX_BOOKING_DURATION_DAYS:
            raise ValueError(
                f"Booking duration cannot exceed {MAX_BOOKING_DURATION_DAYS} days"
            )

        # Max advance booking
        max_advance_date = datetime.now(UTC).date() + timedelta(
            days=MAX_ADVANCE_BOOKING_DAYS
        )
        if self.check_in > max_advance_date:
            raise ValueError(
                f"Bookings cannot be made more than {MAX_ADVANCE_BOOKING_DAYS} days in advance"
            )

        return self


class BookingCreateResponse(BaseModel):
    booking_id: uuid.UUID
    payment_id: uuid.UUID
    status: BookingStatus
    total_amount: Decimal = Field(..., gt=0)
    expires_at: datetime
    razorpay_order_id: str
    razorpay_key_id: str


class BookingResponse(BookingBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    guest_id: uuid.UUID
    property_manager_id: uuid.UUID
    status: BookingStatus
    base_amount: Decimal
    commission_amount: Decimal
    total_amount: Decimal
    expires_at: datetime
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookingWithPaymentResponse(BookingResponse):
    """Booking with payment details."""

    payments: list[PaymentResponse] = []


class BookingListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[BookingResponse]
