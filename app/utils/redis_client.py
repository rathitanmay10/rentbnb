"""Redis client for caching and ephemeral data storage."""

from redis.asyncio import Redis, from_url

from app.core.settings import settings


class RedisClient:
    """Singleton Redis client wrapper."""

    _client: Redis | None = None

    @classmethod
    def get_client(cls) -> Redis:
        """Get or create Redis client."""
        if cls._client is None:
            cls._client = from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return cls._client

    @classmethod
    async def close(cls):
        """Close Redis connection."""
        if cls._client:
            await cls._client.close()
            cls._client = None

    @classmethod
    async def set(cls, key: str, value: str, expire: int | None = None):
        """Set value with optional expiration."""
        client = cls.get_client()
        await client.set(key, value, ex=expire)

    @classmethod
    async def get(cls, key: str) -> str | None:
        """Get value by key."""
        client = cls.get_client()
        return await client.get(key)

    @classmethod
    async def delete(cls, *keys: str):
        client = cls.get_client()
        await client.delete(*keys)

    @classmethod
    async def incr(cls, key: str) -> int:
        """Increment value by 1."""
        client = cls.get_client()
        return await client.incr(key)

    @classmethod
    async def expire(cls, key: str, seconds: int):
        client = cls.get_client()
        await client.expire(key, seconds)

    @classmethod
    async def ttl(cls, key: str) -> int:
        """Return TTL (time-to-live) in seconds."""
        client = cls.get_client()
        return await client.ttl(key)


redis_client = RedisClient()
