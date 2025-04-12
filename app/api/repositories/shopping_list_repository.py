from app.database.supabase_client import SupabaseClient
from app.api.dtos.shopping_list_dtos import ShoppingListDTO, CreateShoppingListDTO


class ShoppingListRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "shopping_list"

    async def create_shopping_list(self, shopping_list_dto: CreateShoppingListDTO) -> ShoppingListDTO:
        result = await self.client.upsert(self.table, shopping_list_dto.model_dump())
        return ShoppingListDTO(**result)

    async def get_shopping_lists_by_user_id(self, user_id: int) -> list[ShoppingListDTO]:
        result = await self.client.read(self.table, {"user_id": user_id})
        return [ShoppingListDTO(**recipe_rating) for recipe_rating in result]
