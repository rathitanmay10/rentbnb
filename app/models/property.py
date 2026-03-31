import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums.property_category import PropertyCategory
from app.models.base import Base
from app.models.mixins import TenantMixin

if TYPE_CHECKING:
    from app.models.amenity import Amenity
    from app.models.booking import Booking
    from app.models.property_image import PropertyImage
    from app.models.review import Review
    from app.models.tenant import Tenant
    from app.models.user import User


class Property(Base, TenantMixin):
    __tablename__ = "properties"

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

    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)

    category: Mapped[PropertyCategory] = mapped_column(
        SAEnum(PropertyCategory, native_enum=False), nullable=False, index=True
    )

    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_night: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), index=True, nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="properties")
    manager: Mapped["User"] = relationship("User", foreign_keys=[managed_by])
    images: Mapped[list["PropertyImage"]] = relationship(
        "PropertyImage",
        back_populates="property",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    amenities: Mapped[list["Amenity"]] = relationship(
        "Amenity",
        secondary="property_amenities",
        back_populates="properties",
        lazy="selectin",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="property", lazy="noload"
    )
    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="property", lazy="noload"
    )
