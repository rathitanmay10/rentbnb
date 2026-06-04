"""Celery periodic task schedule constants."""

# Payment reconciliation - runs every 2 minutes
PAYMENT_RECONCILIATION_INTERVAL_SECONDS = 120.0

# Expired-pending booking sweeper - runs every 5 minutes. Safety net for the
# per-booking expiry task: if its eta task is lost (broker restart) or never
# scheduled (crash mid-create), this reclaims the blocked availability.
EXPIRED_BOOKING_SWEEP_INTERVAL_SECONDS = 300.0

# Token cleanup - runs every 6 hours at the top of the hour
TOKEN_CLEANUP_CRON_HOUR = "*/6"  # noqa: S105
TOKEN_CLEANUP_CRON_MINUTE = 0
