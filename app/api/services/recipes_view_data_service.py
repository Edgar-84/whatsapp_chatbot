from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.recipes_view_data_dtos import RecipesViewDataDTO
from app.api.services.service_exceptions import RecipesViewDataServiceException
from app.config.logger_settings import get_logger


logger = get_logger(__name__)


class RecipesViewDataService:
    @staticmethod
    async def get_recipes_view_data_by_list_id(
        uow: IUnitOfWork, list_id: list[int]
    ) -> list[RecipesViewDataDTO]:
        """
        Get recipes by list_id
        """
        try:
            async with uow:
                recipes: list[RecipesViewDataDTO] = await uow.recipes_view_data_repository.get_recipes_view_data_by_list_id(list_id)
                logger.info(f"Got next recipes count: {len(recipes)}, {recipes}")
                # recipes_info = []
                # for recipe in recipes:
                #     name = recipe.name if recipe.name is not None else ""
                #     sub_title = recipe.sub_title if recipe.sub_title is not None else ""
                #     meal_type = recipe.meal_type if recipe.meal_type is not None else ""
                #     minutes = recipe.minutes if recipe.minutes is not None else ""
                #     preparation_method = recipe.preparation_method if recipe.preparation_method is not None else ""
                #     ingredients = recipe.ingredients if recipe.ingredients is not None else ""
                #     nut_recommend = recipe.nut_recommend if recipe.nut_recommend is not None else ""
                #     comment = recipe.comment if recipe.comment is not None else ""

                #     recipe_details = (
                #         f"*Name:* {name}\n"
                #         f"*Sub title:* {sub_title}\n"
                #         f"*Meal type:* {meal_type}\n"
                #         f"*Minutes:* {minutes}\n"
                #         f"*Preparation Method:*\n{preparation_method}\n"
                #         f"*Ingredients:*\n{ingredients}\n"
                #         f"*Nut recommend:*\n{nut_recommend}\n"
                #         f"*Comment:*\n{comment}\n\n"
                #     )
                #     recipes_info.append(recipe_details)
                
                return recipes

        except Exception as e:
            raise RecipesViewDataServiceException(e)
