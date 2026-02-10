import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from sqlalchemy.sql import func


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def soft_delete(self):
        """Mark object as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self):
        """Undo soft delete."""
        self.is_deleted = False
        self.deleted_at = None


class TenantMixin:
    @declared_attr
    def tenant_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
        )
