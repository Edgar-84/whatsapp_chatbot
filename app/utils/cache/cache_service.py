from cachetools import TTLCache
import asyncio

class UserCache:
    def __init__(self, maxsize=1000, ttl=300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = asyncio.Lock()

    async def get(self, key):
        async with self.lock:
            return self.cache.get(key)

    async def set(self, key, value):
        async with self.lock:
            self.cache[key] = value

    async def __contains__(self, key):
        async with self.lock:
            return key in self.cache

    async def delete(self, key):
        async with self.lock:
            self.cache.pop(key, None)


class UserStates:
    def __init__(self):
        self.states = TTLCache(maxsize=1000, ttl=300)
        self.lock = asyncio.Lock()

    async def get(self, key, default=None):
        async with self.lock:
            return self.states.get(key, default)

    async def set(self, key, value):
        async with self.lock:
            self.states[key] = value

    async def __contains__(self, key):
        async with self.lock:
            return key in self.states

    async def delete(self, key):
        async with self.lock:
            self.states.pop(key, None)

