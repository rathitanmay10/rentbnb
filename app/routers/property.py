import logging
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.constants.rate_limit import (
    PROPERTY_LIST_LIMIT_SECONDS,
    PROPERTY_LIST_LIMIT_TIMES,
)
from app.dependencies import require_roles
from app.dependencies.rate_limit import RateLimiter
from app.dependencies.types import DbDep, TenantIdDep, TenantUserDep
from app.enums import PropertyCategory, UserRole
from app.models.user import User
from app.schemas.error import (
    BAD_REQUEST,
    FORBIDDEN,
    NOT_FOUND,
)
from app.schemas.property import (
    AvailabilityResponse,
    PropertyCreate,
    PropertyListResponse,
    PropertyResponse,
    PropertyUpdate,
)
from app.schemas.property_image import PropertyImageCreateResponse
from app.services import property_service

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/properties", tags=["Properties"], responses={**NOT_FOUND, **FORBIDDEN}
)

PropertyManagerDep = Annotated[
    User, Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.MANAGER))
]


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property(
    data: PropertyCreate,
    user: PropertyManagerDep,
    db: DbDep,
):
    result = await property_service.create_property(db, user, data)
    logger.info(f"Property created: {result.id} by user {user.id}")
    return result


@router.get("/own", response_model=PropertyListResponse)
async def list_own_properties(
    user: PropertyManagerDep,
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """
    List properties for internal users (Tenant Admin, Manager).
    - Tenant Admin: Sees all properties in their tenant.
    - Manager: Sees only properties assigned to them.
    """
    properties, total = await property_service.list_own_properties(
        db, user, skip, limit
    )
    return {"total": total, "skip": skip, "limit": limit, "data": properties}


@router.get("/", response_model=PropertyListResponse, responses={**BAD_REQUEST})
async def list_properties(
    db: DbDep,
    tenant_id: TenantIdDep,
    _: Annotated[
        None,
        Depends(
            RateLimiter(
                times=PROPERTY_LIST_LIMIT_TIMES, seconds=PROPERTY_LIST_LIMIT_SECONDS
            )
        ),
    ],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    category: PropertyCategory | None = Query(None),
    city: str | None = Query(None),
    guests: int | None = Query(None, ge=1),
):
    properties, total = await property_service.list_properties(
        db,
        skip=skip,
        limit=limit,
        min_price=min_price,
        max_price=max_price,
        category=category,
        city=city,
        guests=guests,
        tenant_id=tenant_id,
    )
    return {"total": total, "skip": skip, "limit": limit, "data": properties}


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: UUID,
    user: TenantUserDep,
    db: DbDep,
):
    return await property_service.get_property_for_user(db, property_id, user)


@router.patch("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: UUID,
    data: PropertyUpdate,
    user: PropertyManagerDep,
    db: DbDep,
):
    result = await property_service.update_property(db, user, property_id, data)
    logger.info(f"Property updated: {property_id} by user {user.id}")
    return result


@router.delete(
    "/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**BAD_REQUEST},
)
async def delete_property(
    property_id: UUID,
    user: PropertyManagerDep,
    db: DbDep,
) -> None:
    await property_service.delete_property(db, user, property_id)
    logger.info(f"Property deleted: {property_id} by user {user.id}")


@router.post(
    "/{property_id}/images",
    response_model=PropertyImageCreateResponse,
    responses={**BAD_REQUEST},
)
async def upload_image(
    property_id: UUID,
    user: PropertyManagerDep,
    db: DbDep,
    file: UploadFile = File(...),
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
    db: DbDep,
    user: PropertyManagerDep,
) -> None:
    await property_service.delete_property_image(db, user, property_id, image_id)
    logger.info(
        f"Image {image_id} deleted for property {property_id} by user {user.id}"
    )


@router.get(
    "/{property_id}/check_availability",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_200_OK,
)
async def check_property_availability(
    property_id: UUID,
    check_in: date,
    check_out: date,
    db: DbDep,
    user: TenantUserDep,
):
    available = await property_service.check_availability(
        db, property_id, check_in, check_out, user
    )
    return {"available": available}
