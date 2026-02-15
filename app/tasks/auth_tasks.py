import logging

from app.celery_app import celery_app
from app.crud.blacklist_crud import cleanup_expired_tokens
from app.tasks.base import db_async_task

logger = logging.getLogger(__name__)


@celery_app.task
@db_async_task
async def cleanup_tokens(db):
    """
    Celery task to clean up expired blacklisted tokens.
    Runs periodically via Celery Beat.
    """
    count = await cleanup_expired_tokens(db)
    logger.info(f"Cleaned up {count} expired blacklisted tokens")
    return f"Deleted {count} expired tokens"
