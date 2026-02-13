import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import MessageType


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    sender_id: uuid.UUID | None
    content: str
    message_type: MessageType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageListResponse(BaseModel):
    total: int
    data: list[MessageResponse]
