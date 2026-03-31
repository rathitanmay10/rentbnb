from enum import StrEnum


class WebhookEvents(StrEnum):
    PAYMENT_CAPTURED = "payment.captured"
    PAYMENT_FAILED = "payment.failed"
    REFUND_PROCESSED = "refund.processed"
    REFUND_CREATED = "refund.created"
    REFUND_FAILED = "refund.failed"
