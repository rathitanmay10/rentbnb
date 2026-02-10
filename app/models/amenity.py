import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Amenity(Base):
    __tablename__ = "amenities"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Relationships
    properties = relationship(
        "Property", secondary="property_amenities", back_populates="amenities"
    )


class PropertyAmenity(Base):
    __tablename__ = "property_amenities"

    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True
    )
    amenity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("amenities.id", ondelete="CASCADE"), primary_key=True
    )
