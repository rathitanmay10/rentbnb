from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import booking_crud
from app.database.init_db import get_db
from app.dependencies.user import get_current_user
from app.models import User
from app.schemas.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    BookingWithPaymentResponse,
)
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Response model is dict because it includes payment_order_id which is not in BookingResponse
    # or create a specialized schema
    return await booking_service.create_booking(db, current_user, booking_data)


@router.get("/my", response_model=BookingListResponse)
async def list_my_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bookings = await booking_crud.get_bookings(
        db,
        skip=skip,
        limit=limit,
        guest_id=current_user.id if current_user.role == "guest" else None,
        tenant_id=current_user.tenant_id,
        # For manager/admin we might want different filters
    )
    total = await booking_crud.get_bookings_count(
        db,
        guest_id=current_user.id if current_user.role == "guest" else None,
        tenant_id=current_user.tenant_id,
    )
    return {"total": total, "skip": skip, "limit": limit, "data": bookings}


@router.get("/{booking_id}", response_model=BookingWithPaymentResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await booking_crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.cancel_booking(db, booking_id, current_user)
