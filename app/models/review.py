from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithoutSoftDelete
from app.models.mixins import TenantMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.property import Property
    from app.models.tenant import Tenant
    from app.models.user import User


class Review(BaseWithoutSoftDelete, TenantMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="rating_valid"),
    )

    booking_id: Mapped[UUID] = mapped_column(
        ForeignKey("bookings.id"), unique=True, nullable=False
    )
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("properties.id"), nullable=False
    )
    guest_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)

    booking: Mapped["Booking"] = relationship("Booking", back_populates="review")
    property: Mapped["Property"] = relationship("Property", back_populates="reviews")
    guest: Mapped["User"] = relationship("User", foreign_keys=[guest_id])
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="reviews")
