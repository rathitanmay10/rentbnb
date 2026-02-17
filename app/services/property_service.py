import os
import uuid
from datetime import UTC, datetime
from uuid import UUID

import aiofiles
import aiofiles.os
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.property import MAX_SIZE
from app.crud import booking_crud, property_crud, user_crud
from app.enums import UserRole
from app.models.user import User
from app.schemas.property import PropertyCreate

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


async def create_property(db: AsyncSession, user: User, data: PropertyCreate) -> dict:
    """Create a new property."""
    if user.role not in [UserRole.TENANT_ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create properties",
        )

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
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found"
                )
            if manager.tenant_id != user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Manager does not belong to the same tenant",
                )

    property_data["managed_by"] = target_manager_id

    return await property_crud.create_property(db, property_data)


async def delete_property(db: AsyncSession, user: User, property_id: UUID):
    """Delete a property."""
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )
    if not can_edit_property(user, prop):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this property",
        )
    booking = await booking_crud.get_bookings(
        db,
        tenant_id=user.tenant_id,
        property_id=prop.id,
        check_in=datetime.now(UTC).date(),
        active=True,
    )
    if booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property has future bookings, cannot delete",
        )
    await property_crud.delete_property(db, prop)


async def upload_property_image(
    db: AsyncSession, user: User, property_id: UUID, file: UploadFile
):
    """Upload an image for a property."""
    property_obj = await property_crud.get_property(db, property_id)
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )

    # Auth check
    if not can_edit_property(user, property_obj):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    # Validate file type
    allowed_types = ["image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG and PNG are allowed.",
        )

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
                if size > MAX_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="File size exceeds limit",
                    )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    if not can_edit_property(user, image.property):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

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
