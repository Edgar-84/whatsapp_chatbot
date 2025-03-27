from abc import ABC, abstractmethod

from app.database.supabase_client import SupabaseClient
from app.api.repositories.user_repository import UserRepository
from app.api.repositories.foods_repository import FoodRepository


class IUnitOfWork(ABC):
    user_repository: UserRepository
    food_repository: FoodRepository

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, *args):
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass


class UnitOfWork(IUnitOfWork):
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.user_repository = UserRepository(self.client)
        self.food_repository = FoodRepository(self.client)

    async def __aenter__(self):
        # Here we don't have to initialize a session, as SupabaseClient is the connection.
        return self

    async def __aexit__(self, *args):
        # Here you can handle cleanup, but there's no explicit transaction management in Supabase.
        # If Supabase supports transactions, you can implement it here.
        pass

    async def commit(self):
        # In Supabase, there isn't a manual commit like in SQLAlchemy. Operations are automatically 
        # committed after they are executed.
        pass

    async def rollback(self):
        # Similarly, Supabase doesn't have a built-in rollback mechanism, so if any operations fail,
        # you'd need to manually handle the rollback (e.g., through error handling).
        pass
