from threading import Lock
from typing import Any, List, Dict
from abc import ABC, abstractmethod
from pydantic import BaseModel
from supabase import AsyncClient, acreate_client

from app.config.logger_settings import get_logger


class SupabaseSettings(BaseModel):
   url: str
   key: str
   
   class Config:
       env_prefix = "SUPABASE_"


class ISupabaseClient(ABC):
   @abstractmethod
   async def create(self, table: str, data: dict) -> Dict[str, Any]:
       pass
       
   @abstractmethod
   async def read(self, table: str, query: dict) -> List[Dict[str, Any]]:
       pass
       
   @abstractmethod
   async def update(self, table: str, query: dict, data: dict) -> Dict[str, Any]:
       pass
       
   @abstractmethod
   async def delete(self, table: str, query: dict) -> bool:
       pass


class SupabaseClient(ISupabaseClient):
    _instance = None
    _lock = Lock()
    _client: AsyncClient = None
    _logger = get_logger("supabase_client")

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, settings: SupabaseSettings = None):
        pass

    @classmethod
    async def initialize(cls, settings: SupabaseSettings) -> None:
        if not cls._instance:
            cls._instance = SupabaseClient(settings)
        if not cls._instance._client:
            cls._logger.info("Initializing Supabase client")
            try:
                cls._instance._client = await acreate_client(
                    supabase_url=settings.url,
                    supabase_key=settings.key,
                )
                cls._logger.info("Supabase client initialized successfully")
            except Exception as e:
                cls._logger.error(f"Failed to initialize Supabase client: {e}")
                raise

    @classmethod
    async def get_client(cls) -> AsyncClient:
        if not cls._instance:
           raise Exception("Client not initialized")
        return cls._instance._client

    async def create(self, table: str, data: dict) -> Dict[str, Any]:
        try:
           result = await self._client.table(table).insert(data).execute()
           return result.data[0]

        except Exception as e:
           self._logger.error(f"\x1b[31m Create operation failed: {e}")
           raise

    async def read(self, table: str, query: dict) -> List[Dict[str, Any]]:
        try:
           db_query = self._client.table(table).select("*")
           for key, value in query.items():
               if isinstance(value, dict) and "in" in value:
                   db_query = db_query.in_(key, value["in"])
               else:
                   db_query = db_query.eq(key, value)

           result = await db_query.execute()
           return result.data

        except Exception as e:
           self._logger.error(f"Read operation failed: {e}")
           raise

    async def update(self, table: str, query: dict, data: dict) -> Dict[str, Any]:
        try:
           db_query = self._client.table(table).update(data)
           for key, value in query.items():
               db_query = db_query.eq(key, value)
           
           result = await db_query.execute()
           return result.data[0]

        except Exception as e:
           self._logger.error(f"Update operation failed: {e}")
           raise
    
    async def upsert(self, table: str, data: dict) -> Dict[str, Any]:
        try:
            result = await self._client.table(table).upsert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            self._logger.error(f"Upsert operation failed: {e}")
            raise

    async def delete(self, table: str, query: dict) -> bool:
        try:
           db_query = self._client.table(table).delete()
           for key, value in query.items():
               db_query = db_query.eq(key, value)
           
           result = await db_query.execute()
           return bool(result.data)

        except Exception as e:
           self._logger.error(f"Delete operation failed: {e}")
           raise

    async def filter(self, table: str, select_query: str, filters: List[dict]) -> List[Dict[str, Any]]:
        try:
            db_query = self._client.table(table).select(select_query)

            for filter_item in filters:
                if filter_item.get('foreign_key'):

                    db_query = db_query.filter(
                        filter_item['column'],
                        filter_item.get('operator', 'eq'),
                        filter_item['value']
                    )
                else:
                    db_query = db_query.eq(filter_item['column'], filter_item['value'])
            
            result = await db_query.execute()
            return result.data

        except Exception as e:
            self._logger.error(f"Filter operation failed: {e}")
            raise

    async def close(self):
        """Close the database connection"""
        with self._lock:
            if self._client:
                try:
                    self._client = None
                    self.__class__._instance = None
                    self._logger.info("Database connection closed")
                except Exception as e:
                    self._logger.error(f"Error closing database connection: {e}")
                    raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
