from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud, property_crud
from app.database.init_db import get_db
from app.dependencies import (
    get_current_user,
    get_tenant_user,
    require_roles,
    verify_tenant_property_access,
)
from app.enums import UserRole
from app.models.user import User
from app.schemas.property import (
    PropertyCreate,
    PropertyListResponse,
    PropertyResponse,
    PropertyUpdate,
)
from app.services import property_service

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    return await property_service.create_property(db, user, data)


@router.get("/own", response_model=PropertyListResponse)
async def list_own_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    """
    List properties for internal users (Tenant Admin, Manager).
    - Tenant Admin: Sees all properties in their tenant.
    - Manager: Sees only properties assigned to them.
    """
    properties, total = await property_crud.get_properties_for_user(
        db, user, skip, limit
    )
    return {"total": total, "skip": skip, "limit": limit, "data": properties}


@router.get("/", response_model=PropertyListResponse)
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Decimal = Query(None),
    max_price: Decimal = Query(None),
    category: str = Query(None),
    city: str = Query(None),
    guests: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id
    properties, total = await property_crud.get_properties(
        db, skip, limit, min_price, max_price, category, city, guests, tenant_id
    )
    return {"total": total, "skip": skip, "limit": limit, "data": properties}


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    user: User = Depends(get_tenant_user),
    db: AsyncSession = Depends(get_db),
):
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    verify_tenant_property_access(user, prop)
    return prop


@router.patch("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    data: PropertyUpdate,
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if not property_service.can_edit_property(user, prop):
        raise HTTPException(
            status_code=403, detail="Not authorized to edit this property"
        )

    return await property_crud.update_property(db, prop, data)


@router.post("/{property_id}/images")
async def upload_image(
    property_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    return await property_service.upload_property_image(db, user, property_id, file)


@router.delete(
    "/{property_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_property_image(
    property_id: UUID,
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
):
    await property_service.delete_property_image(db, user, property_id, image_id)


@router.get("/{property_id}/check_availability", status_code=status.HTTP_200_OK)
async def check_property_availability(
    property_id: UUID,
    check_in: date,
    check_out: date,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_tenant_user),
):
    prop = await property_crud.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    verify_tenant_property_access(user, prop)
    booked = await booking_crud.check_availability(db, prop.id, check_in, check_out)
    if booked:
        availability = False
    else:
        availability = True
    return {"available": availability}
