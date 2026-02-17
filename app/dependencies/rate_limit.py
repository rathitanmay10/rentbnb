from fastapi import HTTPException, Request, status

from app.utils.redis_client import redis_client


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

        current_count = await redis.get(key)

        if current_count:
            if int(current_count) >= self.times:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too Many Requests",
                    headers={"Retry-After": str(self.seconds)},
                )
            await redis.incr(key)
        else:
            await redis.set(key, 1, ex=self.seconds)
