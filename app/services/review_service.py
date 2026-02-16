from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, property_crud, review_crud
from app.enums import BookingStatus
from app.models.user import User
from app.schemas.review import (
    PropertyReviewListResponse,
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)


async def create_review(
    db: AsyncSession, review: ReviewCreate, booking_id: UUID, current_user: User
) -> ReviewResponse:
    booking = await booking_crud.get_booking_with_review(
        db, booking_id, current_user.id
    )
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    if booking.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to review this booking",
        )
    if booking.status != BookingStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking must be confirmed to be reviewed",
        )
    if booking.check_out > datetime.now(UTC).date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking must be completed to be reviewed",
        )
    if booking.review is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking has already been reviewed",
        )
    review_obj = await review_crud.create_review(
        db,
        review,
        booking_id=booking_id,
        property_id=booking.property_id,
        guest_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )

    property_obj = await property_crud.get_property(db, review_obj.property_id)
    property_obj.rating = (
        property_obj.rating * property_obj.review_count + review.rating
    ) / (property_obj.review_count + 1)
    property_obj.review_count += 1
    await db.commit()
    return review_obj


async def get_reviews_by_property_id(
    db: AsyncSession,
    property_id: UUID,
    current_user: User,
    skip: int = 0,
    limit: int = 10,
    rating: int | None = None,
) -> PropertyReviewListResponse:
    property_obj = await property_crud.get_property(db, property_id)
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    if property_obj.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Property not found")
    reviews, total = await review_crud.get_reviews_by_property_id(
        db,
        tenant_id=current_user.tenant_id,
        property_id=property_id,
        skip=skip,
        limit=limit,
        rating=rating,
    )
    return PropertyReviewListResponse(
        total=total,
        skip=skip,
        limit=limit,
        data=reviews,
    )


async def get_review_by_id(
    db: AsyncSession,
    review_id: UUID,
    current_user: User,
) -> ReviewResponse:
    review = await review_crud.get_review_by_id(db, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    if review.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return review


async def update_review(
    db: AsyncSession,
    review_id: UUID,
    review_update: ReviewUpdate,
    current_user: User,
) -> ReviewResponse:
    review_obj = await review_crud.get_review_by_id(db, review_id)
    if review_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    if review_obj.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    if review_obj.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this review",
        )
    old_rating = review_obj.rating
    review = await review_crud.update_review(db, review_id, review_update)
    if review.rating != old_rating:
        property_obj = await property_crud.get_property(db, review_obj.property_id)
        if property_obj.review_count > 0:
            property_obj.rating = (
                property_obj.rating * property_obj.review_count
                - old_rating
                + review.rating
            ) / (property_obj.review_count)
    await db.commit()
    return review


async def delete_review(
    db: AsyncSession,
    review_id: UUID,
    current_user: User,
) -> None:
    review_obj = await review_crud.get_review_by_id(db, review_id)
    if review_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    if review_obj.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    if review_obj.guest_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this review",
        )
    await review_crud.delete_review(db, review_id)
    property_obj = await property_crud.get_property(db, review_obj.property_id)
    if property_obj.review_count > 1:
        property_obj.rating = (
            property_obj.rating * property_obj.review_count - review_obj.rating
        ) / (property_obj.review_count - 1)
        property_obj.review_count -= 1
    else:
        property_obj.rating = 0
        property_obj.review_count = 0
    await db.commit()
    return None
