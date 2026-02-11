from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import UserRole
from app.models.amenity import Amenity
from app.models.property import Property
from app.models.property_image import PropertyImage
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyUpdate


async def create_property(db: AsyncSession, property_data: PropertyCreate) -> Property:
    amenities = property_data.pop("amenities", [])
    db_property = Property(**property_data)

    if amenities:
        # Fetch amenities to associate
        result = await db.execute(select(Amenity).filter(Amenity.id.in_(amenities)))
        amenities = result.scalars().all()
        db_property.amenities = list(amenities)

    db.add(db_property)
    await db.commit()
    await db.refresh(db_property)

    return db_property


async def get_property(db: AsyncSession, property_id: UUID) -> Property | None:
    query = (
        select(Property)
        .options(selectinload(Property.images), selectinload(Property.amenities))
        .filter(Property.id == property_id, not Property.is_deleted)
    )

    result = await db.execute(query)
    return result.scalars().first()


async def get_property_by_location(
    db: AsyncSession, latitude: str, longitude: str
) -> Property | None:
    query = select(Property).filter(
        Property.latitude == latitude,
        Property.longitude == longitude,
        not Property.is_deleted,
    )
    result = await db.execute(query)
    return result.scalars().first()


async def update_property(
    db: AsyncSession, property_obj: Property, update_data: PropertyUpdate
) -> Property:
    # Update simple fields
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"amenities"})
    for key, value in update_dict.items():
        setattr(property_obj, key, value)

    # Update amenities if provided
    if update_data.amenities is not None:
        result = await db.execute(
            select(Amenity).filter(Amenity.id.in_(update_data.amenities))
        )
        amenities = result.scalars().all()
        property_obj.amenities = list(amenities)

    await db.commit()
    await db.refresh(property_obj)

    return property_obj


async def delete_property(db: AsyncSession, property_obj: Property):
    property_obj.soft_delete()
    await db.commit()


async def get_properties(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    category: str | None = None,
    city: str | None = None,
    guests: int | None = None,
    tenant_id: UUID | None = None,
) -> tuple[list[Property], int]:

    query = select(Property).filter(
        Property.is_deleted.is_(False), Property.is_active.is_(True)
    )
    if tenant_id:
        query = query.filter(Property.tenant_id == tenant_id)
    if min_price:
        query = query.filter(Property.price_per_night >= min_price)
    if max_price:
        query = query.filter(Property.price_per_night <= max_price)
    if category:
        query = query.filter(Property.category == category)
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if guests:
        query = query.filter(Property.max_guests >= guests)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Pagination and Relations
    query = (
        query.options(selectinload(Property.images), selectinload(Property.amenities))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    return list(result.scalars().all()), total


async def add_property_image(
    db: AsyncSession, property_id: UUID, url: str
) -> PropertyImage:
    image = PropertyImage(property_id=property_id, url=url)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def get_image(
    db: AsyncSession, image_id: UUID, property_id: UUID
) -> PropertyImage | None:
    query = (
        select(PropertyImage)
        .options(selectinload(PropertyImage.property))
        .filter(PropertyImage.id == image_id, PropertyImage.property_id == property_id)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_properties_for_user(
    db: AsyncSession, user: User, skip: int = 0, limit: int = 10
) -> tuple[list[Property], int]:
    query = select(Property).filter(
        Property.is_deleted.is_(False), Property.tenant_id == user.tenant_id
    )

    if user.role == UserRole.MANAGER:
        query = query.filter(Property.managed_by == user.id)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Pagination
    query = (
        query.options(selectinload(Property.images), selectinload(Property.amenities))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def delete_image(db: AsyncSession, image: PropertyImage):
    await db.delete(image)
    await db.commit()


async def soft_delete_properties_by_tenant(db: AsyncSession, tenant_id: UUID) -> None:
    """Soft delete all properties belonging to a tenant."""
    stmt = (
        update(Property)
        .where(Property.tenant_id == tenant_id)
        .where(Property.is_deleted.is_(False))
        .values(is_deleted=True, deleted_at=datetime.now(UTC))
    )
    await db.execute(stmt)
