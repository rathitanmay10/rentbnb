from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import amenity_crud
from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.amenity import Amenity


async def list_amenities(db: AsyncSession) -> list[Amenity]:
    return await amenity_crud.get_all_amenities(db)


async def create_amenity(db: AsyncSession, name: str) -> Amenity:
    if await amenity_crud.get_amenity_by_name(db, name):
        raise ConflictError("Amenity already exists")
    return await amenity_crud.create_amenity(db, name)


async def get_amenity(db: AsyncSession, amenity_id: UUID) -> Amenity:
    amenity = await amenity_crud.get_amenity(db, amenity_id)
    if amenity is None:
        raise NotFoundError("Amenity not found")
    return amenity


async def update_amenity(db: AsyncSession, amenity_id: UUID, name: str) -> Amenity:
    if not await amenity_crud.get_amenity(db, amenity_id):
        raise NotFoundError("Amenity not found")
    existing = await amenity_crud.get_amenity_by_name(db, name)
    if existing and existing.id != amenity_id:
        raise ConflictError("Amenity already exists")
    return await amenity_crud.update_amenity(db, amenity_id, name)


async def delete_amenity(db: AsyncSession, amenity_id: UUID) -> None:
    try:
        await amenity_crud.delete_amenity(db, amenity_id)
    except ValueError as e:
        raise BadRequestError(str(e)) from e
