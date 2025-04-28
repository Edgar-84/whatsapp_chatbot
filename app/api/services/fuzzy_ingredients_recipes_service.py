from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.fuzzy_ingredients_recipes_dtos import FuzzyIngredientsRecipesDTO
from app.api.services.service_exceptions import FuzzyIngredientsRecipesServiceException 


logger = get_logger(__name__)


class FuzzyIngredientsRecipesService:
    @staticmethod
    async def get_list_ingridients_he_en(uow: IUnitOfWork) -> list[str] | None:
        """
        Get all ingredients on Hebrew and English
        """

        try:
            async with uow:
                ingredients: list[FuzzyIngredientsRecipesDTO] = await uow.fuzzy_ingredients_recipes_repository.get_all_fuzzy_ingredients_recipes()
                result_he = [ing.ingredient_he for ing in ingredients]
                result_en = [ing.ingredient_en for ing in ingredients]
                logger.info(f"Result_he count: {len(result_he)}")
                logger.info(f"Result_en count: {len(result_en)}")
                result = []
                result.extend(result_he)
                result.extend(result_en)
                return result

        except Exception as e:
            raise FuzzyIngredientsRecipesServiceException(e)

    @staticmethod
    async def get_recipes_by_ingredients(uow: IUnitOfWork, ingredients: list[str]) -> list[int] | None:
        """
        Get recipes by ingredients names
        """
        try:
            async with uow:
                logger.info(f"Start search recipes with ingredients: {ingredients}")
                ingredients: list[FuzzyIngredientsRecipesDTO] = await uow.fuzzy_ingredients_recipes_repository.get_recipes_by_ingredients(ingredients)
                result = []
                for ing in ingredients:
                    result.extend(ing.recipe_id_list)
                
                logger.info(f"Recipes result: {result}")
                return result

        except Exception as e:
            raise FuzzyIngredientsRecipesServiceException(e)
