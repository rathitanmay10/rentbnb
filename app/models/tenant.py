from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import TenantStatus
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.message import Message
    from app.models.payment import Payment
    from app.models.property import Property
    from app.models.review import Review
    from app.models.user import User
    from app.models.webhook import Webhook


class Tenant(Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        SAEnum(TenantStatus, native_enum=False),
        default=TenantStatus.ACTIVE,
        nullable=False,
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="tenant", lazy="noload"
    )
    properties: Mapped[list["Property"]] = relationship(
        "Property", back_populates="tenant", lazy="select"
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="tenant", lazy="noload"
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="tenant", lazy="noload"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="tenant", lazy="noload"
    )
    webhooks: Mapped[list["Webhook"]] = relationship(
        "Webhook", back_populates="tenant", lazy="noload"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="tenant", lazy="noload"
    )
