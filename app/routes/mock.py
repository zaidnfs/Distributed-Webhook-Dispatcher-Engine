import asyncio

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.services.rate_limiter import redis_client

router = APIRouter()


@router.post("/success")
async def mock_success(request: Request):
    body = await request.json()
    return {"received": True, "payload": body}


@router.post("/server-error")
async def mock_server_error():
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Simulated downstream 500 error",
    )


@router.post("/rate-limited")
async def mock_rate_limited():
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Simulated downstream 429 rate limit",
    )


@router.post("/timeout")
async def mock_timeout():
    await asyncio.sleep(15)
    return {"received": True, "note": "delayed response"}


@router.post("/fail-then-succeed")
async def mock_fail_then_succeed(
    x_webhook_job_id: str = Header(default="default"),
):
    key = f"mock:attempts:{x_webhook_job_id}"
    attempts = redis_client.incr(key)
    redis_client.expire(key, 300)

    if attempts <= 2:
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulated failure on attempt {attempts}",
        )
    return {"received": True, "succeeded_on_attempt": attempts}