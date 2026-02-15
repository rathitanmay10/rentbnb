import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseWithoutSoftDelete

if TYPE_CHECKING:
    from app.models.property import Property


class Amenity(Base):
    __tablename__ = "amenities"
    __table_args__ = (
        Index(
            "uq_amenity_name_active",
            "name",
            unique=True,
            postgresql_where=text("is_deleted IS FALSE"),
        ),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    properties: Mapped[list["Property"]] = relationship(
        "Property", secondary="property_amenities", back_populates="amenities"
    )


class PropertyAmenity(BaseWithoutSoftDelete):
    __tablename__ = "property_amenities"

    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True
    )
    amenity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True
    )
