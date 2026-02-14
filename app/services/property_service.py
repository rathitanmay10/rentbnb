import os
import uuid
from datetime import UTC, datetime
from uuid import UUID

import aiofiles
import aiofiles.os
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, property_crud, user_crud
from app.enums import UserRole
from app.models.user import User
from app.schemas.property import PropertyCreate

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


async def create_property(db: AsyncSession, user: User, data: PropertyCreate) -> dict:
    if user.role not in [UserRole.TENANT_ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create properties",
        )

    property_data = data.model_dump(exclude={"manager_id"})

    existing_property = await property_crud.get_property_by_location(
        db, property_data["latitude"], property_data["longitude"]
    )
    if existing_property:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Property at location {property_data['latitude']}, {property_data['longitude']} already exists.",
        )

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
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not can_edit_property(user, prop):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this property"
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
            status_code=400, detail="Property has future bookings, cannot delete"
        )
    await property_crud.delete_property(db, prop)


async def upload_property_image(
    db: AsyncSession, user: User, property_id: UUID, file: UploadFile
):
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
    os.makedirs(property_dir, exist_ok=True)

    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(property_dir, new_filename)

    async with aiofiles.open(file_path, "wb") as buffer:
        while content := await file.read(1024):
            await buffer.write(content)

    # Save to DB
    url = f"/uploads/{property_id}/{new_filename}"
    return await property_crud.add_property_image(db, property_id, url)


async def delete_property_image(
    db: AsyncSession, user: User, property_id: UUID, image_id: UUID
):
    image = await property_crud.get_image(db, image_id, property_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    if not can_edit_property(user, image.property):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    # Delete file from filesystem
    # URL format: /uploads/{property_id}/{filename}
    # We need to reconstruct the file path.
    # Assuming UPLOAD_DIR is "uploads" and structure is uploads/{property_id}/{filename}

    try:
        filename = image.url.split("/")[-1]
        property_id = str(image.property_id)
        # Construct path safely
        file_path = os.path.join(UPLOAD_DIR, property_id, filename)

        # Use aiofiles.os for async file operations
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
    except Exception as e:
        raise e
    await property_crud.delete_image(db, image)


def can_edit_property(user: User, property_obj) -> bool:
    if user.tenant_id != property_obj.tenant_id:
        return False
    if user.role == UserRole.TENANT_ADMIN:
        return True
    if user.role == UserRole.MANAGER and property_obj.managed_by == user.id:
        return True
    return False
