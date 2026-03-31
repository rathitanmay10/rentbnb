"""Celery periodic task schedule constants."""

# Payment reconciliation - runs every 2 minutes
PAYMENT_RECONCILIATION_INTERVAL_SECONDS = 120.0

# Token cleanup - runs every 6 hours at the top of the hour
TOKEN_CLEANUP_CRON_HOUR = "*/6"  # noqa: S105
TOKEN_CLEANUP_CRON_MINUTE = 0
