import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import WebhookJob
from app.schemas import (
    DeliveryLogResponse,
    WebhookDispatchRequest,
    WebhookDispatchResponse,
)
from app.workers.delivery import deliver_webhook

router = APIRouter()


@router.post(
    "/dispatch",
    response_model=WebhookDispatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def dispatch_webhook(
    request: WebhookDispatchRequest,
    db: Session = Depends(get_db),
    ):

    job_id = str(uuid.uuid4())

    job = WebhookJob(
        id=job_id,
        event_id=request.eventId,
        destination_url=str(request.destinationUrl),
        payload=request.payload,
        status="queued",
    )
    db.add(job)
    db.commit()

    deliver_webhook.delay(job_id)

    
    return WebhookDispatchResponse(status="queued", jobId=job_id)

@router.get("/jobs/{job_id}", response_model=DeliveryLogResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(WebhookJob).filter(WebhookJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = f"Job {job_id} not found",
        )
    return job


@router.get("/logs", response_model=list[DeliveryLogResponse])
def get_delivery_logs(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(WebhookJob)
    if status_filter:
        query = query.filter(WebhookJob.status == status_filter)
    return query.order_by(WebhookJob.created_at.desc()).limit(limit).all()
    