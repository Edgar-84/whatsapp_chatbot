from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.recipe_ratings_dtos import CreateRecipeRatingDTO, RecipeRatingsDTO
from app.api.services.service_exceptions import RecipeRatingsServiceException


logger = get_logger(__name__)


class RecipeRatingsService:
    @staticmethod
    async def create_recipe_rating(uow: IUnitOfWork, recipe_rating: CreateRecipeRatingDTO) -> RecipeRatingsDTO:
        try:
            async with uow:
                recipe_rating = await uow.recipe_ratings_repository.create_recipe_rating(recipe_rating)
                return recipe_rating

        except Exception as e:
            logger.warning(f"Failed to create recipe rating: {e}")
            return None
            # raise RecipeRatingsServiceException(e)

    @staticmethod
    async def get_disliked_recipes_by_user_id(uow: IUnitOfWork, user_id: int) -> list[RecipeRatingsDTO]:
        try:
            async with uow:
                recipes = await uow.recipe_ratings_repository.get_recipe_ratings_by_user_id(user_id=user_id)
                return [recipe for recipe in recipes if recipe.rating == 1]

        except Exception as e:
            logger.warning(f"Failed to 'get_disliked_recipes_by_user_id': {e}")
            return []
