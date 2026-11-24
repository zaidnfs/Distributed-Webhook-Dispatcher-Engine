from pydantic import BaseModel, HttpUrl


class WebhookDispatchRequest(BaseModel):
    destinationUrl: HttpUrl
    eventId: str
    payload: dict

class WebhookDispatchResponse(BaseModel):
    status: str
    jobId: str