from app.database.supabase_client import SupabaseClient
from app.api.dtos.recipes_view_data_dtos import RecipesViewDataDTO
from app.config.logger_settings import get_logger

logger = get_logger(__name__)

class RecipesViewDataRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "recipes_view_data"

    async def get_recipes_view_data_by_list_id(self, list_id: list[int]) -> list[RecipesViewDataDTO]:
        result = await self.client.read(table=self.table, query={"id": {"in": list_id}})
        return [RecipesViewDataDTO(**data) for data in result]
