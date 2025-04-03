from app.database.supabase_client import SupabaseClient
from app.api.dtos.meal_type_dtos import MealTypeDTO


class MealTypeRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "meal_type"

    async def get_all_meal_types(self) -> list[MealTypeDTO]:
        result = await self.client.read(self.table, {})
        return [MealTypeDTO(**meal_type) for meal_type in result]
