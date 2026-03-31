from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.init_db import get_db
from app.dependencies import require_roles, require_super_admin
from app.enums import UserRole
from app.models import User
from app.schemas.dashboard import PlatformDashboardResponse, TenantDashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def validate_dates(from_date: date | None, to_date: date | None) -> None:
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date",
        )


@router.get("/tenant", response_model=TenantDashboardResponse)
async def get_tenant_dashboard(
    from_date: date | None = Query(None, description="Start date for metrics"),
    to_date: date | None = Query(None, description="End date for metrics"),
    current_user: User = Depends(require_roles(UserRole.TENANT_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tenant dashboard metrics.

    Requires TENANT_ADMIN role and active tenant.

    All metrics are filtered by the date range (defaults to current month if not provided).

    Returns:
    - total_revenue: Total revenue from paid payments in date range
    - live_bookings: Bookings active within the date range (check-in <= to_date AND check-out > from_date)
    - active_checkins: Bookings checking in within the date range
    - active_guests: Distinct guests with bookings in the date range
    """

    validate_dates(from_date, to_date)
    return await dashboard_service.get_tenant_dashboard(
        db, current_user.tenant_id, from_date, to_date
    )


@router.get("/platform", response_model=PlatformDashboardResponse)
async def get_platform_dashboard(
    from_date: date | None = Query(None, description="Start date for revenue metrics"),
    to_date: date | None = Query(None, description="End date for revenue metrics"),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get platform dashboard metrics.

    Requires SUPER_ADMIN role.

    All metrics are filtered by the date range (defaults to current month if not provided).

    Returns:
    - total_tenants: Total active tenants (not deleted)
    - total_revenue: Total platform revenue from paid payments in date range
    - bookings_in_range: Bookings created within the date range
    """
    validate_dates(from_date, to_date)
    return await dashboard_service.get_platform_dashboard(db, from_date, to_date)
