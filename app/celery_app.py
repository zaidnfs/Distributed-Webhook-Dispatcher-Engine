from celery import Celery

from app.config import settings

celery = Celery(
    "webhook_dispatcher",
    broker=settings.CELERY_BROKER_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery.autodiscover_tasks(["app.workers"])