import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import WebhookJob
from app.schemas import WebhookDispatchRequest, WebhookDispatchResponse
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