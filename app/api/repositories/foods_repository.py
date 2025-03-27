from app.database.supabase_client import SupabaseClient
from app.api.dtos.food_dtos import FoodDTO


class FoodRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "foods"
    
    async def get_food(self, query: dict) -> FoodDTO | None:
        result = await self.client.read(self.table, query)
        if len(result) == 0:
            return None
        return FoodDTO(**result[0])

    async def get_foods_by_list_lab_codes(self, lab_codes: list[str]) -> list[FoodDTO]:
        result = await self.client.read(self.table, {"lab_code": {"in": lab_codes}})
        return [FoodDTO(**food) for food in result] if result else []
