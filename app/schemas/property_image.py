import uuid
from datetime import datetime

from pydantic import BaseModel


class PropertyImageResponse(BaseModel):
    id: uuid.UUID
    url: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PropertyImageCreateResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    url: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
