from app.config.logger_settings import get_logger
from app.database.supabase_client import SupabaseClient
from app.api.dtos.recipes_dtos import RecipeDTO

logger = get_logger(__name__)


class RecipesRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "recipes"

    async def get_recipes_by_meal_type(self, meal_type_id: int) -> list[RecipeDTO]:
        """Get list products for selected meal type"""
        logger.debug(f"Getting recipes by meal type: {meal_type_id}")
        result = await self.client.read(
            "recipes_meal_type", 
            {"meal_type_id": meal_type_id}
        )
        recipe_ids = [row["recipe_id"] for row in result] if result else []
        logger.debug(f"Recipe ids: {recipe_ids}")
        if not recipe_ids:
            return []
        
        recipes = await self.client.read(self.table, {"id": {"in": recipe_ids}})
        return [RecipeDTO(**recipe) for recipe in recipes] if recipes else []

    async def get_foods_by_recipes(self, recipe_ids: list[int]) -> dict[int, list[int]]:
        """Get dictionary {recipe_id: [list of food.]}"""
        if not recipe_ids:
            return {}

        result = await self.client.read(
            "recipes_foods", 
            {"recipe_id": {"in": recipe_ids}}
        )
        
        recipe_food_map = {}
        for row in result:
            recipe_food_map.setdefault(row["recipe_id"], []).append(row["food_id"])
        
        return recipe_food_map
