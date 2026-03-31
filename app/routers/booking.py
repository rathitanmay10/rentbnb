import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud
from app.database.init_db import get_db
from app.dependencies.permissions import require_roles
from app.dependencies.tenant import get_tenant_user
from app.enums import BookingStatus, UserRole
from app.models import User
from app.schemas.booking import (
    BookingCreate,
    BookingCreateResponse,
    BookingListResponse,
    BookingResponse,
    BookingWithPaymentResponse,
)
from app.services import booking_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post(
    "/", response_model=BookingCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(require_roles(UserRole.GUEST)),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new booking
    """
    result = await booking_service.create_booking(db, current_user, booking_data)
    logger.info(
        f"Booking created: {result['booking_id']} for property {booking_data.property_id}"
    )
    return result


@router.get("/my", response_model=BookingListResponse)
async def list_my_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: BookingStatus | None = Query(None),
    property_id: UUID | None = Query(None),
    check_in: date | None = Query(None),
    check_out: date | None = Query(None),
    current_user: User = Depends(get_tenant_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all bookings for the current user
    """
    bookings = await booking_crud.get_bookings(
        db,
        skip=skip,
        limit=limit,
        guest_id=current_user.id if current_user.role == UserRole.GUEST else None,
        property_manager_id=current_user.id
        if current_user.role == UserRole.MANAGER
        else None,
        tenant_id=current_user.tenant_id,
        status=status,
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
    )
    total = await booking_crud.get_bookings_count(
        db,
        guest_id=current_user.id if current_user.role == UserRole.GUEST else None,
        property_manager_id=current_user.id
        if current_user.role == UserRole.MANAGER
        else None,
        tenant_id=current_user.tenant_id,
        status=status,
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
    )
    return {"total": total, "skip": skip, "limit": limit, "data": bookings}


@router.get("/{booking_id}", response_model=BookingWithPaymentResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_tenant_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a booking by ID
    """
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    if booking.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    current_user: User = Depends(get_tenant_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a booking
    """
    result = await booking_service.cancel_booking(db, booking_id, current_user)
    logger.info(f"Booking cancelled: {booking_id} by user {current_user.id}")
    return result
