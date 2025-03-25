from app.database.supabase_client import SupabaseClient
from app.api.dtos.user_dtos import UserDTO


class UserRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "users"
    
    async def get_user(self, query: dict) -> UserDTO | None:
        result = await self.client.read(self.table, query)
        if len(result) == 0:
            return None
        return UserDTO(**result[0])

    async def update_user(self, query: dict, data: dict) -> UserDTO:
        result = await self.client.update(self.table, query, data)
        return UserDTO(**result)
