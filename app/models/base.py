from app.database import Base as DeclarativeBase
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin


class Base(UUIDMixin, TimestampMixin, SoftDeleteMixin, DeclarativeBase):
    __abstract__ = True
