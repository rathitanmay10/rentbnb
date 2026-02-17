from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging

from app.config.settings import settings
from app.core.logger import setup_logging as app_setup_logging


@setup_logging.connect
def config_loggers(*args, **kwargs):
    app_setup_logging()


celery_app = Celery(
    "rentbnb",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.booking_tasks",
        "app.tasks.payment_tasks",
        "app.tasks.email_tasks",
        "app.tasks.auth_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry on startup configuration
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "reconcile-pending-payments": {
            "task": "app.tasks.payment_tasks.reconcile_pending_payments",
            "schedule": 120.0,  # Run every 2 minutes
        },
        "cleanup-expired-tokens": {
            "task": "app.tasks.auth_tasks.cleanup_tokens",
            "schedule": crontab(minute=0, hour="*/6"),  # Run every 6 hours
        },
    },
)
