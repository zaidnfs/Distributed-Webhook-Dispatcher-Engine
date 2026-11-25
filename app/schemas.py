from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class WebhookDispatchRequest(BaseModel):
    destinationUrl: HttpUrl
    eventId: str
    payload: dict

class WebhookDispatchResponse(BaseModel):
    status: str
    jobId: str

class DeliveryLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    destination_url: str
    status: str
    attempt_count: int
    http_status_code: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    last_attempt_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None