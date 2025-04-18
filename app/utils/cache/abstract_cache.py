from abc import ABC, abstractmethod

class AbstractUserCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> dict | None:
        pass

    @abstractmethod
    async def set(self, key: str, value: dict) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def contains(self, key: str) -> bool:
        pass

