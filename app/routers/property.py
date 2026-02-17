import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.rate_limit import (
    PROPERTY_LIST_LIMIT_SECONDS,
    PROPERTY_LIST_LIMIT_TIMES,
)
from app.crud import booking_crud, property_crud
from app.database.init_db import get_db
from app.dependencies import (
    get_tenant_id_from_header,
    get_tenant_user,
    require_roles,
    verify_tenant_property_access,
)
from app.dependencies.rate_limit import RateLimiter
from app.enums import PropertyCategory, UserRole
from app.models.user import User
from app.schemas.property import (
    PropertyCreate,
    PropertyListResponse,
    PropertyResponse,
    PropertyUpdate,
)
from app.schemas.property_image import PropertyImageCreateResponse
from app.services import property_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/properties", tags=["Properties"])


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await property_service.create_property(db, user, data)
    logger.info(f"Property created: {result.id} by user {user.id}")
    return result


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
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    category: PropertyCategory | None = Query(None),
    city: str | None = Query(None),
    guests: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_id_from_header),
    _: None = Depends(
        RateLimiter(
            times=PROPERTY_LIST_LIMIT_TIMES, seconds=PROPERTY_LIST_LIMIT_SECONDS
        )
    ),
):
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID is required"
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )
    verify_tenant_property_access(user, prop)
    if not property_service.can_edit_property(user, prop):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this property",
        )

    result = await property_crud.update_property(db, prop, data)
    logger.info(f"Property updated: {property_id} by user {user.id}")
    return result


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID,
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    await property_service.delete_property(db, user, property_id)
    logger.info(f"Property deleted: {property_id} by user {user.id}")
    return


@router.post("/{property_id}/images", response_model=PropertyImageCreateResponse)
async def upload_image(
    property_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    result = await property_service.upload_property_image(db, user, property_id, file)
    logger.info(f"Image uploaded for property {property_id} by user {user.id}")
    return result


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
    logger.info(
        f"Image {image_id} deleted for property {property_id} by user {user.id}"
    )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Property not found"
        )
    verify_tenant_property_access(user, prop)
    booked = await booking_crud.check_availability(db, prop.id, check_in, check_out)
    if booked:
        availability = False
    else:
        availability = True
    return {"available": availability}
