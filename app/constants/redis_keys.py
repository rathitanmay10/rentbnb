"""Redis key patterns and helper functions."""

from uuid import UUID


def get_tenant_prefix(tenant_id: UUID | None) -> str:
    """
    Get tenant-scoped Redis key prefix.

    Args:
        tenant_id: Tenant UUID or None for non-tenant keys

    Returns:
        Tenant prefix string for Redis keys
    """
    return f"tenant:{tenant_id}:" if tenant_id else "tenant:none:"


# Redis key templates (use with tenant prefix)
REDIS_VERIFICATION_EMAIL = "verification:{email}"
REDIS_VERIFICATION_TOKEN = "verification:{token}"  # noqa: S105
REDIS_RESET_EMAIL = "reset:{email}"
REDIS_RESET_TOKEN = "reset:{token}"  # noqa: S105
REDIS_OTP = "otp:{email}"
REDIS_OTP_COOLDOWN = "otp_cooldown:{email}"
REDIS_OTP_ATTEMPTS = "otp_attempts:{email}"
