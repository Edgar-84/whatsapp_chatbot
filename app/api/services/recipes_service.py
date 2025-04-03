from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.recipes_dtos import RecipeDTO
from app.api.services.service_exceptions import RecipesServiceException
from app.config.logger_settings import get_logger


logger = get_logger(__name__)


class RecipesService:
    @staticmethod
    async def get_recipes_without_forbidden_foods(
        uow: IUnitOfWork, meal_type_id: int, forbidden_foods: list[int]
    ) -> list[RecipeDTO]:
        """
        Get recipes for meal_type_id, excluding those containing forbidden foods.
        """
        try:
            logger.debug(f"Getting recipes by meal type: {meal_type_id}")
            async with uow:
                # 1. Get recipes by meal type
                recipes = await uow.recipe_repository.get_recipes_by_meal_type(meal_type_id)
                recipe_ids = [r.id for r in recipes]
                
                if not recipe_ids:
                    return []
                logger.info(f"Recipe ids len: {len(recipe_ids)}")
                logger.debug(f"Recipe ids: {recipe_ids}")
                # 2. Get foods for each recipe
                recipe_food_map = await uow.recipe_repository.get_foods_by_recipes(recipe_ids)
                logger.info(f"Recipe food map len: {len(recipe_food_map)}")
                logger.debug(f"Recipe food map: {recipe_food_map}")
                # 3. Filter recipes, excluding those containing forbidden foods
                allowed_recipes = [
                    recipe for recipe in recipes
                    if not any(food_id in forbidden_foods for food_id in recipe_food_map.get(recipe.id, []))
                ]
                logger.info(f"Allowed recipes len: {len(allowed_recipes)}")
                logger.debug(f"Allowed recipes: {[r.id for r in allowed_recipes]}")
                return allowed_recipes

        except Exception as e:
            raise RecipesServiceException(e)
