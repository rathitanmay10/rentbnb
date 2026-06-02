from uuid import UUID

from fastapi import APIRouter, Query, status

from app.dependencies.types import DbDep, GuestUserDep, TenantUserDep
from app.schemas.review import (
    PropertyReviewListResponse,
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)
from app.services import review_service

router = APIRouter(prefix="", tags=["Reviews"])


@router.post(
    "/bookings/{booking_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    booking_id: UUID,
    review: ReviewCreate,
    db: DbDep,
    current_user: GuestUserDep,
):
    return await review_service.create_review(db, review, booking_id, current_user)


@router.get(
    "/properties/{property_id}/reviews",
    response_model=PropertyReviewListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_reviews_by_property_id(
    property_id: UUID,
    db: DbDep,
    current_user: TenantUserDep,
    skip: int = 0,
    limit: int = 10,
    rating: int | None = Query(default=None, ge=1, le=5),
):
    return await review_service.get_reviews_by_property_id(
        db,
        property_id=property_id,
        current_user=current_user,
        skip=skip,
        limit=limit,
        rating=rating,
    )


@router.get(
    "/reviews/{review_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
)
async def get_review_by_id(
    review_id: UUID,
    db: DbDep,
    current_user: TenantUserDep,
):
    return await review_service.get_review_by_id(db, review_id, current_user)


@router.patch(
    "/reviews/{review_id}",
    response_model=ReviewResponse,
    status_code=status.HTTP_200_OK,
)
async def update_review(
    review_id: UUID,
    review: ReviewUpdate,
    db: DbDep,
    current_user: GuestUserDep,
):
    return await review_service.update_review(db, review_id, review, current_user)


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_review(
    review_id: UUID,
    db: DbDep,
    current_user: GuestUserDep,
) -> None:
    await review_service.delete_review(db, review_id, current_user)
