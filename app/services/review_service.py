from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, property_crud, review_crud
from app.enums import BookingStatus
from app.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.user import User
from app.schemas.review import (
    PropertyReviewListResponse,
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)


async def _refresh_property_rating(
    db: AsyncSession, property_id: UUID, tenant_id: UUID
) -> None:
    """Recompute a property's rating/review_count from the reviews table.

    Locks the property row first so concurrent review mutations serialize and
    cannot lose an update; the aggregate is recomputed from source (no drift).
    """
    property_obj = await property_crud.get_property_with_lock(
        db, property_id, tenant_id
    )
    if property_obj is None:
        return
    avg_rating, review_count = await review_crud.get_property_rating_stats(
        db, property_id, tenant_id
    )
    property_obj.rating = avg_rating
    property_obj.review_count = review_count


async def create_review(
    db: AsyncSession, review: ReviewCreate, booking_id: UUID, current_user: User
) -> ReviewResponse:
    """Create a review for a booking."""
    booking = await booking_crud.get_booking_with_review(
        db, booking_id, current_user.id
    )
    if booking is None:
        raise NotFoundError("Booking not found")
    if booking.guest_id != current_user.id:
        raise ForbiddenError("You are not authorized to review this booking")
    if booking.status != BookingStatus.CONFIRMED:
        raise BadRequestError("Booking must be confirmed to be reviewed")
    if booking.check_out > datetime.now(UTC).date():
        raise BadRequestError("Booking must be completed to be reviewed")
    if booking.review is not None:
        raise BadRequestError("Booking has already been reviewed")
    review_obj = await review_crud.create_review(
        db,
        review,
        booking_id=booking_id,
        property_id=booking.property_id,
        guest_id=current_user.id,
        tenant_id=current_user.tenant_id,
    )

    await _refresh_property_rating(db, review_obj.property_id, current_user.tenant_id)
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
    """Get reviews for a property."""
    property_obj = await property_crud.get_property(db, property_id)
    if not property_obj:
        raise NotFoundError("Property not found")
    if property_obj.tenant_id != current_user.tenant_id:
        raise NotFoundError("Property not found")
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
    """Get review by ID."""
    review = await review_crud.get_review_by_id(db, review_id)
    if review is None:
        raise NotFoundError("Review not found")
    if review.tenant_id != current_user.tenant_id:
        raise NotFoundError("Review not found")
    return review


async def update_review(
    db: AsyncSession,
    review_id: UUID,
    review_update: ReviewUpdate,
    current_user: User,
) -> ReviewResponse:
    """Update a review."""
    review_obj = await review_crud.get_review_by_id(db, review_id)
    if review_obj is None:
        raise NotFoundError("Review not found")
    if review_obj.tenant_id != current_user.tenant_id:
        raise NotFoundError("Review not found")
    if review_obj.guest_id != current_user.id:
        raise ForbiddenError("You are not authorized to update this review")
    review = await review_crud.update_review(db, review_id, review_update)
    await _refresh_property_rating(db, review_obj.property_id, current_user.tenant_id)
    await db.commit()
    return review


async def delete_review(
    db: AsyncSession,
    review_id: UUID,
    current_user: User,
) -> None:
    """Delete a review."""
    review_obj = await review_crud.get_review_by_id(db, review_id)
    if review_obj is None:
        raise NotFoundError("Review not found")
    if review_obj.tenant_id != current_user.tenant_id:
        raise NotFoundError("Review not found")
    if review_obj.guest_id != current_user.id:
        raise ForbiddenError("You are not authorized to delete this review")
    await review_crud.delete_review(db, review_id)
    await _refresh_property_rating(db, review_obj.property_id, current_user.tenant_id)
    await db.commit()
    return None
