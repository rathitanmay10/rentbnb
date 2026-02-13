import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import MessageType
from app.models.base import BaseWithoutSoftDelete
from app.models.mixins import TenantMixin


class Message(BaseWithoutSoftDelete, TenantMixin):
    __tablename__ = "messages"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,  # Null for system messages
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(
        SAEnum(MessageType, native_enum=False),
        default=MessageType.USER_MESSAGE,
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="messages")
    booking = relationship("Booking", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
