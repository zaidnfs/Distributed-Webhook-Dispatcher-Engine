import uuid

from fastapi import APIRouter, status

from app.schemas import WebhookDispatchRequest, WebhookDispatchResponse

router = APIRouter()


@router.post(
    "/dispatch",
    response_model=WebhookDispatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def dispatch_webhook(request: WebhookDispatchRequest):
    job_id = str(uuid.uuid4())

    return WebhookDispatchResponse(status="queued", jobId=job_id)