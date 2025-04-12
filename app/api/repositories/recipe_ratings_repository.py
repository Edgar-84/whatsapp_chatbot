from app.database.supabase_client import SupabaseClient
from app.api.dtos.recipe_ratings_dtos import RecipeRatingsDTO, CreateRecipeRatingDTO


class RecipeRatingsRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "recipe_ratings"

    async def create_recipe_rating(self, recipe_rating: CreateRecipeRatingDTO) -> RecipeRatingsDTO:
        result = await self.client.upsert(self.table, recipe_rating.model_dump())
        return RecipeRatingsDTO(**result)

    async def get_recipe_ratings_by_user_id(self, user_id: int) -> list[RecipeRatingsDTO]:
        result = await self.client.read(self.table, {"user_id": user_id})
        return [RecipeRatingsDTO(**recipe_rating) for recipe_rating in result]
