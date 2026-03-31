from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Comment cannot be just whitespace")
            if len(v) < 10:
                raise ValueError("Comment must be at least 10 characters long")
        return v


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: int | None = Field(None, ge=1, le=5)
    comment: str | None = Field(None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Comment cannot be just whitespace")
            if len(v) < 10:
                raise ValueError("Comment must be at least 10 characters long")
        return v


class ReviewResponse(ReviewBase):
    id: UUID
    property_id: UUID
    booking_id: UUID
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
    booking_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PropertyReviewListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: list[PropertyReviewResponse]
