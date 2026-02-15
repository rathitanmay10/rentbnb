import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.enums.property_category import PropertyCategory
from app.schemas.amenity import AmenityResponse
from app.schemas.property_image import PropertyImageResponse


class PropertyBase(BaseModel):
    name: str
    description: str | None = None
    address: str
    city: str
    state: str
    country: str
    zipcode: str | None = None
    latitude: Decimal
    longitude: Decimal
    category: PropertyCategory
    bedrooms: int
    max_guests: int
    price_per_night: Decimal
    is_active: bool = True


class PropertyCreate(PropertyBase):
    amenities: list[uuid.UUID] = []
    manager_id: uuid.UUID | None = None


class PropertyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    zipcode: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    category: PropertyCategory | None = None
    bedrooms: int | None = None
    max_guests: int | None = None
    price_per_night: Decimal | None = None
    is_active: bool | None = None
    amenities: list[uuid.UUID] | None = None


class PropertyResponse(PropertyBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    managed_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    rating: Decimal
    review_count: int
    images: list[PropertyImageResponse] = []
    amenities: list[AmenityResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PropertyListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[PropertyResponse]
