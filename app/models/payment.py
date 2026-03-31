import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.payment import DEFAULT_CURRENCY
from app.enums import PaymentStatus
from app.models.base import BaseWithoutSoftDelete
from app.models.mixins import TenantMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.tenant import Tenant
    from app.models.user import User


class Payment(BaseWithoutSoftDelete, TenantMixin):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_non_negative"),
        Index("ix_payments_tenant_status", "tenant_id", "status"),
        Index("ix_payments_created_at", "created_at"),
    )

    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id"), nullable=False, index=True
    )
    guest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, native_enum=False),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10), default=DEFAULT_CURRENCY, nullable=False
    )

    razorpay_order_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="payments")
    booking: Mapped["Booking"] = relationship("Booking", back_populates="payments")
    guest: Mapped["User"] = relationship("User", foreign_keys=[guest_id])
