from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import amenity_crud
from app.database.init_db import get_db
from app.dependencies import get_current_user, require_super_admin
from app.models.user import User
from app.schemas.amenity import (
    AmenityCreate,
    AmenityListResponse,
    AmenityResponse,
    AmenityUpdate,
)

router = APIRouter(prefix="/amenities", tags=["Amenities"])


@router.get("/", response_model=AmenityListResponse)
async def list_amenities(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    List all amenities
    """
    return await amenity_crud.get_all_amenities(db)


@router.post("/", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(
    data: AmenityCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new amenity
    """
    if await amenity_crud.get_amenity_by_name(db, data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amenity already exists"
        )
    return await amenity_crud.create_amenity(db, data.name)


@router.get("/{id}", response_model=AmenityResponse)
async def get_amenity_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get an amenity by ID
    """
    return await amenity_crud.get_amenity(db, id)


@router.put("/{id}", response_model=AmenityResponse)
async def update_amenity_by_id(
    id: int,
    data: AmenityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Update an amenity by ID
    """
    if await amenity_crud.get_amenity_by_name(db, data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Amenity already exists"
        )
    return await amenity_crud.update_amenity(db, id, data.name)


@router.delete(
    "/{id}", response_model=AmenityResponse, status_code=status.HTTP_204_NO_CONTENT
)
async def delete_amenity_by_id(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Delete an amenity by ID
    """
    try:
        return await amenity_crud.delete_amenity(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
