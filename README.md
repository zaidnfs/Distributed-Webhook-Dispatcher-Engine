# Distributed Webhook Dispatcher

An asynchronous webhook delivery service built with FastAPI, Celery, Redis, and PostgreSQL. It accepts webhook events, returns `202 Accepted` immediately, delivers payloads in the background, retries transient failures with exponential backoff, and enforces per-domain rate limits.

## Live Deployment

- Base URL: `https://distributed-webhook-dispatcher-engine-production.up.railway.app`
- API Docs: `https://distributed-webhook-dispatcher-engine-production.up.railway.app/docs`

## Stack

- **API:** FastAPI + Pydantic
- **Queue / Worker:** Celery + Redis
- **Database:** PostgreSQL (SQLite for local dev) + SQLAlchemy
- **HTTP Client:** `httpx`
- **Tests:** `pytest`

## Architecture & Design Choices

- **Non-blocking ingestion:** `POST /api/webhooks/dispatch` validates the payload, writes a `queued` job record to PostgreSQL, pushes the job ID to Redis via Celery, and returns `202 Accepted` immediately. Slow or failing downstream servers never block the API.
- **Background execution & state persistence:** Separate API and Celery worker processes share PostgreSQL as the source of truth (`queued` -> `retrying` -> `success` / `failed`), tracking `attempt_count`, `http_status_code`, `error_message`, `last_attempt_at`, and `next_retry_at`.
- **Retries & backoff:** Transient errors (`5xx`, `429`, timeouts, connection errors) are retried up to 3 times using exponential backoff (`2s`, `4s`, `8s`) plus `0-1s` random jitter to avoid synchronized retry bursts. Non-retryable `4xx` responses (other than `429`) fail immediately.
- **Per-domain rate limiting:** Before each delivery, the worker runs an atomic Redis Lua token-bucket script keyed by destination domain (`ratelimit:{domain}`, default 5 req/s). Throttled jobs are re-queued with a 1-second delay without consuming error retries.

## Endpoints

- `POST /api/webhooks/dispatch` - Queue a webhook for delivery (`202 Accepted`)
- `GET /api/webhooks/jobs/{job_id}` - Check status and delivery details for a job
- `GET /api/webhooks/logs?status=failed&limit=20` - List recent delivery jobs
- `POST /api/mock/success` - Mock receiver returning `200`
- `POST /api/mock/fail-then-succeed` - Returns `500` on first 2 attempts per job, then `200`
- `POST /api/mock/timeout` - Sleeps 15s to simulate a downstream timeout
- `POST /api/mock/server-error` - Always returns `500`
- `POST /api/mock/rate-limited` - Always returns `429`

## Testing the Live API

### 1. Happy path
```bash
curl -X POST https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/webhooks/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "destinationUrl": "https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/mock/success",
    "eventId": "evt_001",
    "payload": {"event": "user.signup", "userId": "usr_999"}
  }'
```

### 2. Retry with exponential backoff (fails twice, succeeds on 3rd attempt)
```bash
curl -X POST https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/webhooks/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "destinationUrl": "https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/mock/fail-then-succeed",
    "eventId": "evt_002",
    "payload": {"event": "payment.failed"}
  }'
```

### 3. Non-blocking timeout test (returns 202 immediately while target sleeps 15s)
```bash
curl -X POST https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/webhooks/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "destinationUrl": "https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/mock/timeout",
    "eventId": "evt_003",
    "payload": {"event": "slow.target"}
  }'
```

### 4. Check job status and logs
```bash
curl https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/webhooks/jobs/<JOB_ID>
curl "https://distributed-webhook-dispatcher-engine-production.up.railway.app/api/webhooks/logs?limit=20"
```

## Running Locally

### With Docker Compose
```bash
docker compose up --build
```

### Without Docker
Requires a running Redis instance.
```bash
python -m venv venv
# Activate venv, then:
pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload
celery -A app.celery_app.celery worker --loglevel=info --pool=solo
```

### Run Tests
```bash
pytest -v
```