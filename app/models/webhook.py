import uuid
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithoutSoftDelete
from app.models.mixins import TenantMixin


class Webhook(BaseWithoutSoftDelete, TenantMixin):
    __tablename__ = "webhooks"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    razorpay_event_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="webhooks")
