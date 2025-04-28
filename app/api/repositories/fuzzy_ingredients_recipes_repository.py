import urllib.parse

from app.database.supabase_client import SupabaseClient
from app.api.dtos.fuzzy_ingredients_recipes_dtos import FuzzyIngredientsRecipesDTO
from app.config.logger_settings import get_logger

logger = get_logger(__name__)

class FuzzyIngredientsRecipesRepository:
    def __init__(self, supabase_client: SupabaseClient):
        self.client = supabase_client
        self.table = "fuzzy_ingredients_recipes"

    async def get_all_fuzzy_ingredients_recipes(self) -> list[FuzzyIngredientsRecipesDTO]:
        result = await self.client.read(table=self.table, query={})
        return [FuzzyIngredientsRecipesDTO(**data) for data in result]

    async def get_recipes_by_ingredients(self, ingredients: list[str]) -> list[FuzzyIngredientsRecipesDTO]:
        if not ingredients:
            return []
        
        result_en = await self.client.read(self.table, {"ingredient_en": {"in": ingredients}})
        result_en_dto = [FuzzyIngredientsRecipesDTO(**data) for data in result_en]
        result_he = await self.client.read(self.table, {"ingredient_he": {"in": ingredients}})
        result_he_dto = [FuzzyIngredientsRecipesDTO(**data) for data in result_he]
        return result_en_dto + result_he_dto
