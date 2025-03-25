from sqlalchemy import insert, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict


class AbstractRepository(ABC):
    @abstractmethod
    async def create(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def update(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def get_single(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, **kwargs):
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, dto_dict: dict) -> int:
        stmt = insert(self.model).values(**dto_dict).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update(self, dto_dict: dict, filters: dict) -> int:
        data = {k: v for k, v in dto_dict.items() if v is not None}     # For check None in Schemes
        stmt = update(self.model).filter_by(**filters).values(data).returning(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete(self, id: int) -> Any:
        stmt = delete(self.model).where(self.model.id == id).returning(self.model)
        await self.session.execute(stmt)

    async def get_multi(self, filters: Optional[Dict[str, Any]] = None):
        stmt = select(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)

        result = await self.session.execute(stmt)
        result = [row[0].to_read_model() for row in result.all()]
        return result

    async def get_single(self, filters: dict):
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        result = result.scalar_one().to_read_model()
        return result
