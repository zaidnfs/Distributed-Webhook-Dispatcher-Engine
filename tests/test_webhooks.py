from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.rate_limiter import extract_domain

client = TestClient(app)


def test_extract_domain():
    assert extract_domain("https://Api.Example.COM/webhook") == "api.example.com"
    assert extract_domain("http://localhost:8000/api/mock/success") == "localhost:8000"


def test_dispatch_webhook_validation_error():
    response = client.post(
        "/api/webhooks/dispatch",
        json={
            "destinationUrl": "not-a-valid-url",
            "eventId": "evt_bad",
            "payload": {"test": True},
        },
    )
    assert response.status_code == 422


@patch("app.routes.webhooks.deliver_webhook.delay")
def test_dispatch_and_get_job_status(mock_delay):
    response = client.post(
        "/api/webhooks/dispatch",
        json={
            "destinationUrl": "https://example.com/hook",
            "eventId": "evt_test_123",
            "payload": {"event": "user.signup"},
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "queued"
    job_id = data["jobId"]

    mock_delay.assert_called_once_with(job_id)

    # Verify GET /jobs/{job_id}
    status_res = client.get(f"/api/webhooks/jobs/{job_id}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "queued"
    assert status_res.json()["event_id"] == "evt_test_123"


def test_get_unknown_job_returns_404():
    response = client.get("/api/webhooks/jobs/non-existent-id")
    assert response.status_code == 404


@patch("app.workers.delivery.allow_request", return_value=True)
@patch("app.workers.delivery.httpx.post")
@patch("app.routes.webhooks.deliver_webhook.delay")
def test_worker_delivery_success(mock_delay, mock_post, mock_rate_limit):
    # First create a job via API
    res = client.post(
        "/api/webhooks/dispatch",
        json={
            "destinationUrl": "https://example.com/hook",
            "eventId": "evt_worker_ok",
            "payload": {"ok": True},
        },
    )
    job_id = res.json()["jobId"]

    # Mock a 200 OK downstream response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Run the worker function synchronously
    from app.workers.delivery import deliver_webhook
    deliver_webhook(job_id)

    # Verify DB updated to success
    status_res = client.get(f"/api/webhooks/jobs/{job_id}")
    assert status_res.json()["status"] == "success"
    assert status_res.json()["http_status_code"] == 200
    assert status_res.json()["attempt_count"] == 1