import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PropertyImageResponse(BaseModel):
    id: uuid.UUID
    url: str = Field(max_length=1024)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PropertyImageCreateResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    url: str = Field(max_length=1024)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
