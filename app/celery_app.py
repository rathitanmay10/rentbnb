import sys

from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging

from app.config.settings import settings
from app.core.logger import setup_logging as app_setup_logging


@setup_logging.connect
def config_loggers(*args, **kwargs):
    """
    Configure logging for Celery workers and Beat scheduler.
    Uses separate log files based on the process type.
    """
    is_beat = any("beat" in arg.lower() for arg in sys.argv)

    if is_beat:
        app_setup_logging(log_file="logs/beat.log")
    else:
        app_setup_logging(log_file="logs/celery.log")


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
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "reconcile-pending-payments": {
            "task": "app.tasks.payment_tasks.reconcile_pending_payments",
            "schedule": 120.0,
        },
        "cleanup-expired-tokens": {
            "task": "app.tasks.auth_tasks.cleanup_tokens",
            "schedule": crontab(minute=0, hour="*/6"),
        },
    },
)
