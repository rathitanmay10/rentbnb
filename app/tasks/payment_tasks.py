import logging
from uuid import UUID

from app.celery_app import celery_app
from app.constants.payment import PAYMENT_RECONCILIATION_WINDOWS
from app.services import payment_service
from app.tasks.base import db_async_task

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=5)
@db_async_task
async def check_payment_status(db, self, payment_id: str):
    """Check payment status with Razorpay and update if necessary."""

    try:
        await payment_service.check_payment_status(db, UUID(payment_id))
        await db.commit()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


@celery_app.task
@db_async_task
async def reconcile_pending_payments(db):
    """
    Periodic task to check status of pending payments.
    Uses time windows to implement exponential backoff.
    """
    from app.crud import payment_crud

    try:
        payments = await payment_crud.get_payments_to_poll(
            db, PAYMENT_RECONCILIATION_WINDOWS
        )

        for payment in payments:
            check_payment_status.delay(str(payment.id))

    except Exception as exc:
        logger.error(f"Reconciliation task failed: {exc}")


@celery_app.task(bind=True, max_retries=5)
@db_async_task
async def refund_payment_task(db, self, payment_id: str):
    """
    Celery task to process refund for a payment.
    """
    try:
        await payment_service.process_refund(db, UUID(payment_id))
        await db.commit()
    except Exception as exc:
        logger.error(f"Refund task failed for payment {payment_id}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
