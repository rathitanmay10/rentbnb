import uuid

from pydantic import BaseModel


class AmenityCreate(BaseModel):
    name: str


class AmenityResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class AssignAmenitySchema(BaseModel):
    property_id: uuid.UUID
    amenity_ids: list[uuid.UUID]
