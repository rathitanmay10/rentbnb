from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies.types import CurrentUserDep, DbDep, SuperAdminDep
from app.schemas.amenity import (
    AmenityCreate,
    AmenityListResponse,
    AmenityResponse,
    AmenityUpdate,
)
from app.schemas.error import (
    CONFLICT,
    FORBIDDEN,
    NOT_FOUND,
)
from app.services import amenity_service

router = APIRouter(
    prefix="/amenities", tags=["Amenities"], responses={**NOT_FOUND, **FORBIDDEN, **CONFLICT}
)


@router.get("/", response_model=AmenityListResponse)
async def list_amenities(db: DbDep, current_user: CurrentUserDep):
    """
    List all amenities
    """
    amenities = await amenity_service.list_amenities(db)
    total = len(amenities)
    return {"total": total, "data": amenities}


@router.post("/", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(
    data: AmenityCreate,
    current_user: SuperAdminDep,
    db: DbDep,
):
    """
    Create a new amenity
    """
    return await amenity_service.create_amenity(db, data.name)


@router.get("/{id}", response_model=AmenityResponse)
async def get_amenity_by_id(
    id: UUID,
    db: DbDep,
    current_user: CurrentUserDep,
):
    """
    Get an amenity by ID
    """
    return await amenity_service.get_amenity(db, id)


@router.put("/{id}", response_model=AmenityResponse)
async def update_amenity_by_id(
    id: UUID,
    data: AmenityUpdate,
    db: DbDep,
    current_user: SuperAdminDep,
):
    """
    Update an amenity by ID
    """
    return await amenity_service.update_amenity(db, id, data.name)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_amenity_by_id(
    id: UUID,
    db: DbDep,
    current_user: SuperAdminDep,
) -> None:
    """
    Delete an amenity by ID
    """
    await amenity_service.delete_amenity(db, id)
