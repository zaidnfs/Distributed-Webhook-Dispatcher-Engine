from fastapi import FastAPI

from app.db import Base, engine
from app.models import WebhookJob
from app.routes.mock import router as mock_router
from app.routes.webhooks import router as webhook_router

app = FastAPI(title="Distributed Webhook Dispatcher")

Base.metadata.create_all(bind=engine)

app.include_router(webhook_router, prefix="/api/webhooks")
app.include_router(mock_router, prefix="/api/mock", tags=["Mock Receivers"])
