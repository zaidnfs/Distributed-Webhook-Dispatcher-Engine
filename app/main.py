from fastapi import FastAPI

from app.routes.webhooks import router as webhook_router

app = FastAPI(title="Distributed Webhook Dispatcher")

app.include_router(webhook_router, prefix="/api/webhooks")