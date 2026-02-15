import uuid

from pydantic import BaseModel, field_validator

from app.utils.validators import validate_amenity_name


class AmenityCreate(BaseModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        return validate_amenity_name(v)


class AmenityUpdate(BaseModel):
    name: str

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        return validate_amenity_name(v)


class AmenityResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_config = {"from_attributes": True}


class AmenityListResponse(BaseModel):
    total: int
    data: list[AmenityResponse]
