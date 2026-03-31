import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.enums import MessageType


class MessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Content cannot be empty or just whitespace")
        if len(v) > 2000:
            raise ValueError("Content cannot be longer than 2000 characters")
        return v


class MessageResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    sender_id: uuid.UUID | None
    content: str
    message_type: MessageType
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[MessageResponse]
