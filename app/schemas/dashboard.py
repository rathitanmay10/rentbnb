from decimal import Decimal

from pydantic import BaseModel


class TenantDashboardResponse(BaseModel):
    """Response schema for tenant dashboard metrics."""

    total_revenue: Decimal
    live_bookings: int
    active_checkins: int
    active_guests: int


class PlatformDashboardResponse(BaseModel):
    """Response schema for platform dashboard metrics."""

    total_tenants: int
    total_revenue: Decimal
    bookings_in_range: int
