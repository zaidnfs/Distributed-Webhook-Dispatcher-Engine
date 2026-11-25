from sqlalchemy import exc
from datetime import datetime, timezone

import httpx

from app.celery_app import celery
from app.config import settings
from app.db import SessionLocal
from app.models import WebhookJob


@celery.task(name="delivery_webhook")
def deliver_webhook(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(WebhookJob).filter(WebhookJob.id == job_id).first()
        if not job:
            return
        
        try: response = httpx.post(
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
        elif response.status_code == 429 or response.status_code >= 500:
            job.status = "failed"
            job.error_message = response.text[:500]
        else:
            job.status = "failed"
            job.error_message = response.text[:500]

    except (httpx.TimeoutException, httpx.ConnectError) as e:
        job.status = "failed"
        job.attempt_count += 1
        job.last_attempt_at = datetime.now(timezone.utc)
        job.error_message = str(e)[:500]

    db.commit()

finally:
    db.close()
        