from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = None


class ReviewResponse(ReviewBase):
    id: UUID
    property_id: UUID
    guest_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[ReviewResponse]


class PropertyReviewResponse(ReviewBase):
    id: UUID
    guest_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PropertyReviewListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[PropertyReviewResponse]
