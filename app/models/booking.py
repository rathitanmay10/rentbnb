import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import BookingStatus
from app.models.base import BaseWithoutSoftDelete
from app.models.mixins import TenantMixin


class Booking(BaseWithoutSoftDelete, TenantMixin):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("check_in < check_out", name="check_in_before_check_out"),
        CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id"), nullable=False, index=True
    )
    guest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    property_manager_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, native_enum=False),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )

    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=0, nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="bookings")
    property = relationship("Property", back_populates="bookings")
    guest = relationship("User", foreign_keys=[guest_id])
    manager = relationship("User", foreign_keys=[property_manager_id])
    payments = relationship("Payment", back_populates="booking", lazy="selectin")
    messages = relationship(
        "Message", back_populates="booking", cascade="all, delete-orphan"
    )
