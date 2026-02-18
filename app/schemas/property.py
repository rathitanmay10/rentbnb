import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.enums.property_category import PropertyCategory
from app.schemas.amenity import AmenityResponse
from app.schemas.property_image import PropertyImageResponse


class PropertyBase(BaseModel):
    name: str = Field(..., min_length=5, max_length=255)
    description: str | None = Field(None, max_length=2000)
    address: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    country: str = Field(..., max_length=100)
    zipcode: str | None = Field(None, max_length=20)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180)
    category: PropertyCategory
    bedrooms: int = Field(..., ge=1)
    max_guests: int = Field(..., ge=1)
    price_per_night: Decimal = Field(..., gt=0, le=999999.99)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_max_guests(self):
        if self.max_guests > self.bedrooms * 3:
            raise ValueError(
                f"Max guests ({self.max_guests}) cannot exceed 3 times the number of bedrooms ({self.bedrooms})"
            )
        return self


class PropertyCreate(PropertyBase):
    amenities: list[uuid.UUID] = []
    manager_id: uuid.UUID | None = None


class PropertyUpdate(BaseModel):
    name: str | None = Field(None, min_length=5, max_length=255)
    description: str | None = Field(None, max_length=2000)
    address: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    zipcode: str | None = Field(None, max_length=20)
    latitude: Decimal | None = Field(None, ge=-90, le=90)
    longitude: Decimal | None = Field(None, ge=-180, le=180)
    category: PropertyCategory | None = None
    bedrooms: int | None = Field(None, ge=1)
    max_guests: int | None = Field(None, ge=1)
    price_per_night: Decimal | None = Field(None, gt=0, le=999999.99)
    is_active: bool | None = None
    amenities: list[uuid.UUID] | None = None
    managed_by: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_max_guests(self):
        if self.max_guests is not None and self.bedrooms is not None:
            if self.max_guests > self.bedrooms * 3:
                raise ValueError(
                    f"Max guests ({self.max_guests}) cannot exceed 3 times the number of bedrooms ({self.bedrooms})"
                )
        return self


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
    model_config = {"from_attributes": True}


class PropertyListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[PropertyResponse]
