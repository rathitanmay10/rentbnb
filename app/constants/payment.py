# Backoff windows for payment reconciliation
# Format: (min_age_minutes, max_age_minutes)
# We check payments that fall into these age buckets to avoid spamming the provider
PAYMENT_RECONCILIATION_WINDOWS = [
    (2, 5),  # Immediate check: 2-5 mins old
    (10, 15),  # Short-term check: 10-15 mins old
    (30, 40),  # Mid-term check: 30-40 mins old
    (60, 90),  # Hourly check: 1-1.5 hours old
    (600, 700),  # Final check: ~10-12 hours old
]

COMMISSION_PERCENTAGE = 10.0