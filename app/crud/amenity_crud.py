from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.amenity import Amenity


async def create_amenity(db: AsyncSession, name: str) -> Amenity:
    amenity = Amenity(name=name)
    db.add(amenity)
    await db.commit()
    await db.refresh(amenity)
    return amenity


async def get_amenity_by_name(db: AsyncSession, name: str) -> Amenity | None:
    result = await db.execute(select(Amenity).filter(Amenity.name == name))
    return result.scalars().first()


async def get_all_amenities(db: AsyncSession) -> list[Amenity]:
    result = await db.execute(select(Amenity))
    return list(result.scalars().all())


async def get_amenity(db: AsyncSession, amenity_id: UUID) -> Amenity | None:
    return await db.get(Amenity, amenity_id)
