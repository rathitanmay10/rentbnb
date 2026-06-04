from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.amenity import Amenity, PropertyAmenity


async def create_amenity(db: AsyncSession, name: str) -> Amenity:
    amenity = Amenity(name=name)
    db.add(amenity)
    await db.flush()
    await db.refresh(amenity)
    return amenity


async def get_amenity_by_name(db: AsyncSession, name: str) -> Amenity | None:
    result = await db.execute(
        select(Amenity).filter(Amenity.name == name, Amenity.is_deleted.is_(False))
    )
    return result.scalars().first()


async def get_all_amenities(db: AsyncSession) -> list[Amenity]:
    result = await db.execute(select(Amenity).filter(Amenity.is_deleted.is_(False)))
    return list(result.scalars().all())


async def get_amenity(db: AsyncSession, amenity_id: UUID) -> Amenity | None:
    return await db.get(Amenity, amenity_id)


async def update_amenity(
    db: AsyncSession, amenity_id: UUID, name: str
) -> Amenity | None:
    amenity = await get_amenity(db, amenity_id)
    if not amenity:
        return None
    amenity.name = name
    await db.flush()
    await db.refresh(amenity)
    return amenity


async def delete_amenity(db: AsyncSession, amenity_id: UUID) -> None:
    amenity = await get_amenity(db, amenity_id)
    if not amenity:
        return None

    result = await db.execute(
        select(PropertyAmenity).where(PropertyAmenity.amenity_id == amenity_id)
    )
    if result.first():
        raise ValueError("Cannot delete amenity that is in use by properties")

    amenity.soft_delete()
    await db.flush()
