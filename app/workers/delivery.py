import random
from datetime import datetime, timedelta, timezone

import httpx

from app.celery_app import celery
from app.config import settings
from app.db import SessionLocal
from app.models import WebhookJob


@celery.task(
    bind=True, 
    name="deliver_webhook",
    max_retries=settings.MAX_RETRIES)
def deliver_webhook(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(WebhookJob).filter(WebhookJob.id == job_id).first()
        if not job:
            return
        
        try:
            response = httpx.post(
                job.destination_url,
                json=job.payload,
                headers={
                    "X-Webhook-Event-Id": job.event_id,
                    "X-Webhook-Job-Id": job.id,
                },
                timeout=settings.DELIVERY_TIMEOUT_SECONDS,
            )

            job.http_status_code = response.status_code
            job.last_attempt_at = datetime.now(timezone.utc)
            job.attempt_count += 1

            if response.status_code < 300:
                job.status = "success"
                job.next_retry_at = None
                job.error_message = None
                db.commit()
                return

            elif response.status_code == 429 or response.status_code >= 500:
                job.error_message = response.text[:500]
                _retry_or_fail(self, job, db)
                return

            else:
                job.status = "failed"
                job.error_message = response.text[:500]
                db.commit()
                return

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            
            job.attempt_count += 1
            job.last_attempt_at = datetime.now(timezone.utc)
            job.error_message = str(e)[:500]
            _retry_or_fail(self, job, db)
            return

    finally:
        db.close()


def _retry_or_fail(task, job, db):
    """
    Either schedule a retry with backoff, or mark as permanently failed.
    """
    if task.request.retries < settings.MAX_RETRIES:
        delay = settings.BACKOFF_BASE_SECONDS * (2 ** task.request.retries)
        delay += random.uniform(0, 1)

        job.status = "retrying"
        job.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        db.commit()

        raise task.retry(countdown=delay)
    else:
        job.status = "failed"
        job.next_retry_at = None
        db.commit()













