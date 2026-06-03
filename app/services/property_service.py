import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import aiofiles
import aiofiles.os
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.property import MAX_IMAGE_SIZE
from app.crud import booking_crud, property_crud, user_crud
from app.dependencies.tenant import verify_tenant_property_access
from app.enums import PropertyCategory, UserRole
from app.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.property import Property
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyUpdate

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


async def list_own_properties(db: AsyncSession, user: User, skip: int, limit: int):
    """List properties for internal users (Tenant Admin, Manager)."""
    return await property_crud.get_properties_for_user(db, user, skip, limit)


async def list_properties(
    db: AsyncSession,
    *,
    skip: int,
    limit: int,
    min_price: Decimal | None,
    max_price: Decimal | None,
    category: PropertyCategory | None,
    city: str | None,
    guests: int | None,
    tenant_id: UUID | None,
):
    """List public properties for a tenant."""
    if tenant_id is None:
        raise BadRequestError("Tenant ID is required")
    return await property_crud.get_properties(
        db, skip, limit, min_price, max_price, category, city, guests, tenant_id
    )


async def get_property_for_user(
    db: AsyncSession, property_id: UUID, user: User
) -> Property:
    """Fetch a property and verify tenant access."""
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise NotFoundError("Property not found")
    verify_tenant_property_access(user, prop)
    return prop


async def check_availability(
    db: AsyncSession,
    property_id: UUID,
    check_in: date,
    check_out: date,
    user: User,
) -> bool:
    """Check whether a property is available for the given date range."""
    if check_out <= check_in:
        raise BadRequestError("check_out must be after check_in")
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise NotFoundError("Property not found")
    verify_tenant_property_access(user, prop)
    booked = await booking_crud.check_availability(db, prop.id, check_in, check_out)
    return not booked


async def create_property(db: AsyncSession, user: User, data: PropertyCreate) -> dict:
    """Create a new property."""
    if user.role not in [UserRole.TENANT_ADMIN, UserRole.MANAGER]:
        raise ForbiddenError("Not authorized to create properties")

    property_data = data.model_dump(exclude={"manager_id"})

    property_data["tenant_id"] = user.tenant_id

    target_manager_id = data.manager_id

    if user.role == UserRole.MANAGER:
        target_manager_id = user.id
    elif user.role == UserRole.TENANT_ADMIN:
        if not target_manager_id:
            target_manager_id = user.id

        if target_manager_id != user.id:
            manager = await user_crud.get_user(db, target_manager_id)
            if not manager:
                raise NotFoundError("Manager not found")
            if manager.tenant_id != user.tenant_id:
                raise ForbiddenError("Manager does not belong to the same tenant")
            if manager.role not in [UserRole.MANAGER, UserRole.TENANT_ADMIN]:
                raise ForbiddenError("Target user does not have a manager role")

    property_data["managed_by"] = target_manager_id

    return await property_crud.create_property(db, property_data)


async def delete_property(db: AsyncSession, user: User, property_id: UUID):
    """Delete a property."""
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise NotFoundError("Property not found")
    if not can_edit_property(user, prop):
        raise ForbiddenError("Not authorized to delete this property")
    booking = await booking_crud.get_bookings(
        db,
        tenant_id=user.tenant_id,
        property_id=prop.id,
        check_in=datetime.now(UTC).date(),
        active=True,
    )
    if booking:
        raise BadRequestError("Property has future bookings, cannot delete")
    await property_crud.delete_property(db, prop)


async def update_property(
    db: AsyncSession, user: User, property_id: UUID, data: PropertyUpdate
) -> Property:
    """Update a property."""
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise NotFoundError("Property not found")

    if not can_edit_property(user, prop):
        raise ForbiddenError("Not authorized to edit this property")

    # Check if managed_by is being updated
    if data.managed_by:
        if user.role != UserRole.TENANT_ADMIN:
            raise ForbiddenError("Only Tenant Admin can change the property manager")

        # Verify new manager exists and belongs to the same tenant
        new_manager = await user_crud.get_user(db, data.managed_by)
        if not new_manager:
            raise NotFoundError("Manager not found")
        if new_manager.tenant_id != user.tenant_id:
            raise NotFoundError("Manager not found")
        if new_manager.role not in [UserRole.MANAGER, UserRole.TENANT_ADMIN]:
            raise ForbiddenError("Target user does not have a manager role")

    return await property_crud.update_property(db, prop, data)


async def upload_property_image(
    db: AsyncSession, user: User, property_id: UUID, file: UploadFile
):
    """Upload an image for a property."""
    property_obj = await property_crud.get_property(db, property_id)
    if not property_obj:
        raise NotFoundError("Property not found")

    # Auth check
    if not can_edit_property(user, property_obj):
        raise ForbiddenError("Not authorized")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise BadRequestError("Invalid file type. Only JPEG and PNG are allowed.")

    # Save file
    property_dir = os.path.join(UPLOAD_DIR, str(property_id))
    await aiofiles.os.makedirs(property_dir, exist_ok=True)

    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(property_dir, new_filename)

    try:
        size = 0
        async with aiofiles.open(file_path, "wb") as buffer:
            while content := await file.read(64 * 1024):
                size += len(content)
                if size > MAX_IMAGE_SIZE:
                    raise BadRequestError("File size exceeds limit")
                await buffer.write(content)
        url = f"/uploads/{property_id}/{new_filename}"
        return await property_crud.add_property_image(db, property_id, url)
    except Exception:
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
        raise

    # TODO: Add image to S3


async def delete_property_image(
    db: AsyncSession, user: User, property_id: UUID, image_id: UUID
):
    """Delete an image from a property."""
    image = await property_crud.get_image(db, image_id, property_id)
    if not image:
        raise NotFoundError("Image not found")

    if not can_edit_property(user, image.property):
        raise ForbiddenError("Not authorized")

    filename = image.url.split("/")[-1]
    property_id = str(image.property_id)
    file_path = os.path.join(UPLOAD_DIR, property_id, filename)

    if await aiofiles.os.path.exists(file_path):
        await aiofiles.os.remove(file_path)
    await property_crud.delete_image(db, image)


def can_edit_property(user: User, property_obj) -> bool:
    """Check if the user can edit the property."""
    if user.tenant_id != property_obj.tenant_id:
        return False
    if user.role == UserRole.TENANT_ADMIN:
        return True
    if user.role == UserRole.MANAGER and property_obj.managed_by == user.id:
        return True
    return False
