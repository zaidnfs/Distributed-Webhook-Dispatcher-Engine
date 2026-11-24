import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

# from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from app.db import Base


class WebhookJob(Base):
    __tablename__ = "webhook_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, nullable=False)
    destination_url = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="queued", nullable=False)
    attempt_count = Column(Integer, default=0)
    http_status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.UTC))
    last_attempt_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)

