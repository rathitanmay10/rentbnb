from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import amenity_crud
from app.database.init_db import get_db
from app.dependencies import require_super_admin
from app.models.user import User
from app.schemas.amenity import AmenityCreate, AmenityResponse

router = APIRouter(prefix="/amenities", tags=["Amenities"])


@router.get("/", response_model=list[AmenityResponse])
async def list_amenities(db: AsyncSession = Depends(get_db)):
    return await amenity_crud.get_all_amenities(db)


@router.post("/", response_model=AmenityResponse, status_code=status.HTTP_201_CREATED)
async def create_amenity(
    data: AmenityCreate,
    user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    # Only Super Admin
    return await amenity_crud.create_amenity(db, data.name)
