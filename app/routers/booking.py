import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.dependencies.types import DbDep, GuestUserDep, TenantUserDep
from app.enums import BookingStatus
from app.schemas.booking import (
    BookingCreate,
    BookingCreateResponse,
    BookingListResponse,
    BookingResponse,
    BookingWithPaymentResponse,
)
from app.schemas.error import (
    CONFLICT,
    FORBIDDEN,
    NOT_FOUND,
)
from app.services import booking_service

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/bookings", tags=["Bookings"], responses={**NOT_FOUND, **FORBIDDEN}
)


@router.post(
    "/",
    response_model=BookingCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**CONFLICT},
)
async def create_booking(
    booking_data: BookingCreate,
    current_user: GuestUserDep,
    db: DbDep,
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
    current_user: TenantUserDep,
    db: DbDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: BookingStatus | None = Query(None),
    property_id: UUID | None = Query(None),
    check_in: date | None = Query(None),
    check_out: date | None = Query(None),
):
    """
    List all bookings for the current user
    """
    bookings, total = await booking_service.list_bookings_for_user(
        db,
        current_user,
        skip=skip,
        limit=limit,
        status=status,
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
    )
    return {"total": total, "skip": skip, "limit": limit, "data": bookings}


@router.get("/{booking_id}", response_model=BookingWithPaymentResponse)
async def get_booking(
    booking_id: UUID,
    current_user: TenantUserDep,
    db: DbDep,
):
    """
    Get a booking by ID
    """
    return await booking_service.get_booking_for_user(db, booking_id, current_user)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    current_user: TenantUserDep,
    db: DbDep,
):
    """
    Cancel a booking
    """
    result = await booking_service.cancel_booking(db, booking_id, current_user)
    logger.info(f"Booking cancelled: {booking_id} by user {current_user.id}")
    return result
