import logging

from fastapi import HTTPException, Request, status

from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, times: int, seconds: int):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request):
        try:
            client_ip = request.client.host
        except AttributeError:
            client_ip = "127.0.0.1"

        key = f"rate_limit:{client_ip}:{request.url.path}"

        redis = redis_client.get_client()

        # Atomic increment
        current_count = await redis.incr(key)

        # Set TTL only on first request (when key is created)
        if current_count == 1:
            await redis.expire(key, self.seconds)

        if current_count > self.times:
            ttl = await redis.ttl(key)
            # If ttl is -1 (no expiry) or -2 (key doesn't exist), fallback to window size
            retry_after = ttl if ttl and ttl > 0 else self.seconds
            logger.warning(f"Too Many Requests from {client_ip} for {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too Many Requests, Retry-After: {retry_after}",
            )
