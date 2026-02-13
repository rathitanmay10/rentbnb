import asyncio

from app.celery_app import celery_app
from app.services.email_service import email_service


@celery_app.task
def send_email_task(email_to: str, subject: str, body: str):
    """Send email asynchronously via Celery using EmailService."""
    asyncio.run(email_service.send_email(to_email=email_to, subject=subject, body=body))
