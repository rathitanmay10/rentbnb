from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)


async def get_review_by_id(db: AsyncSession, review_id: UUID) -> ReviewResponse | None:
    result = await db.execute(select(Review).where(Review.id == review_id))
    return result.scalar_one_or_none()


async def get_reviews_by_property_id(
    db: AsyncSession,
    tenant_id: UUID,
    property_id: UUID,
    skip: int = 0,
    limit: int = 10,
    rating: int | None = None,
) -> tuple[list[Review], int]:
    query = select(Review).where(
        Review.property_id == property_id, Review.tenant_id == tenant_id
    )
    if rating is not None:
        query = query.where(Review.rating >= rating)
    count_query = select(func.count()).select_from(query.subquery())
    count = (await db.execute(count_query)).scalar_one()
    query = query.offset(skip).limit(limit)
    reviews = (await db.execute(query)).scalars().all()
    return list(reviews), count


async def get_reviews_by_guest_id(
    db: AsyncSession, guest_id: UUID, skip: int = 0, limit: int = 10
) -> list[ReviewResponse]:
    result = await db.execute(
        select(Review).where(Review.guest_id == guest_id).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def create_review(
    db: AsyncSession,
    review: ReviewCreate,
    booking_id: UUID,
    property_id: UUID,
    guest_id: UUID,
    tenant_id: UUID,
) -> Review:
    db_review = Review(
        **review.model_dump(),
        booking_id=booking_id,
        property_id=property_id,
        guest_id=guest_id,
        tenant_id=tenant_id,
    )
    db.add(db_review)
    await db.flush()
    await db.refresh(db_review)
    return db_review


async def update_review(
    db: AsyncSession, review_id: UUID, review: ReviewUpdate
) -> Review | None:
    result = await db.execute(select(Review).where(Review.id == review_id))
    db_review = result.scalar_one_or_none()
    if db_review is None:
        return None
    for field, value in review.model_dump(exclude_unset=True).items():
        setattr(db_review, field, value)
    await db.flush()
    await db.refresh(db_review)
    return db_review


async def delete_review(db: AsyncSession, review_id: UUID) -> bool:
    result = await db.execute(select(Review).where(Review.id == review_id))
    db_review = result.scalar_one_or_none()
    if db_review is None:
        return False
    await db.delete(db_review)
    await db.flush()
    return True
