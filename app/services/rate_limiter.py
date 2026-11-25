import time
from urllib.parse import urlparse

import redis

from app.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call("HMGET", key, "tokens", "last_refill")
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    last_refill = now
else
    local elapsed = math.max(0, now - last_refill)
    tokens = math.min(capacity, tokens + (elapsed * refill_rate))
    last_refill = now
end

if tokens >= 1 then
    tokens = tokens - 1
    redis.call("HMSET", key, "tokens", tokens, "last_refill", last_refill)
    redis.call("EXPIRE", key, math.ceil(capacity / refill_rate) + 10)
    return 1
else
    redis.call("HMSET", key, "tokens", tokens, "last_refill", last_refill)
    redis.call("EXPIRE", key, math.ceil(capacity / refill_rate) + 10)
    return 0
end
"""

_consume_token = redis_client.register_script(TOKEN_BUCKET_LUA)


def extract_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def allow_request(destination_url: str) -> bool:
    domain = extract_domain(destination_url)
    key = f"ratelimit:{domain}"
    rate = settings.RATE_LIMIT_PER_DOMAIN
    allowed = _consume_token(
        keys=[key],
        args=[rate, rate, time.time()]
    )
    return bool(allowed)











