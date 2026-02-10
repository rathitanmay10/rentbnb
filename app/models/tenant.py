from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import TenantStatus
from app.models.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[TenantStatus] = mapped_column(
        SAEnum(TenantStatus, native_enum=False),
        default=TenantStatus.ACTIVE,
        nullable=False,
    )

    users = relationship("User", back_populates="tenant", lazy="noload")
