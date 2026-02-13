from app.database import Base as DeclarativeBase
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin


class BaseWithoutSoftDelete(UUIDMixin, TimestampMixin, DeclarativeBase):
    """Base for models that should never be deleted (historical records)."""

    __abstract__ = True


class Base(BaseWithoutSoftDelete, SoftDeleteMixin):
    """Base for models that support soft delete."""

    __abstract__ = True
