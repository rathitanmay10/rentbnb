import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import UserRole
from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index(
            "uq_tenant_email_active",
            "tenant_id",
            "email",
            unique=True,
            postgresql_where=text("is_deleted IS FALSE"),
        ),
        Index(
            "uq_tenant_username_active",
            "tenant_id",
            "username",
            unique=True,
            postgresql_where=text("is_deleted IS FALSE"),
        ),
    )
    username: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False),
        default=UserRole.GUEST,
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    tenant = relationship("Tenant", back_populates="users", lazy="joined")
    blacklisted_tokens = relationship(
        "BlacklistedToken", back_populates="user", lazy="noload"
    )


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user = relationship("User", back_populates="blacklisted_tokens", lazy="selectin")
