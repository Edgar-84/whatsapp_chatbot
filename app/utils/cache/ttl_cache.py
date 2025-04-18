from cachetools import TTLCache
import asyncio
from typing import Optional
from app.utils.cache.abstract_cache import AbstractUserCache


class InMemoryUserCache(AbstractUserCache):
    def __init__(self, maxsize=1000, ttl=300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[dict]:
        async with self.lock:
            return self.cache.get(key)

    async def set(self, key: str, value: dict) -> None:
        async with self.lock:
            self.cache[key] = value

    async def delete(self, key: str) -> None:
        async with self.lock:
            self.cache.pop(key, None)

    async def contains(self, key: str) -> bool:
        async with self.lock:
            return key in self.cache



class RedisUserCache(AbstractUserCache):
    def __init__(self, redis_client):
        self.redis = redis_client

    async def get(self, key: str) -> Optional[dict]:
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value: dict) -> None:
        await self.redis.set(key, json.dumps(value), ex=300)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def contains(self, key: str) -> bool:
        return await self.redis.exists(key) > 0
