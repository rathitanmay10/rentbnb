import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums.property_category import PropertyCategory
from app.models.base import Base
from app.models.mixins import TenantMixin


class Property(Base, TenantMixin):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "latitude",
            "longitude",
            "is_deleted",
            name="uq_property_lat_lng_deleted",
        ),
    )

    managed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    zipcode: Mapped[str | None] = mapped_column(String(20), nullable=True)

    latitude: Mapped[str] = mapped_column(String(50), nullable=False)
    longitude: Mapped[str] = mapped_column(String(50), nullable=False)

    category: Mapped[PropertyCategory] = mapped_column(
        SAEnum(PropertyCategory, native_enum=False), nullable=False, index=True
    )

    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="properties")
    manager = relationship("User", foreign_keys=[managed_by])
    images = relationship(
        "PropertyImage",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    amenities = relationship(
        "Amenity",
        secondary="property_amenities",
        back_populates="properties",
        lazy="selectin",
    )
    bookings = relationship("Booking", back_populates="property", lazy="noload")
