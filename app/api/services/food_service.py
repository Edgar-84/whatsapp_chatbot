from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.food_dtos import FoodDTO
from app.api.services.service_exceptions import FoodServiceException


logger = get_logger(__name__)


class FoodService:
    @staticmethod
    async def get_foods_by_list_lab_codes(uow: IUnitOfWork, lab_codes: list[str]) -> list[FoodDTO] | None:
        """
        Get all products for list of lab codes
        """
        logger.info(f"Getting foods by list lab codes: {lab_codes}")
        try:
            async with uow:
                foods = await uow.food_repository.get_foods_by_list_lab_codes(lab_codes)
                return foods

        except Exception as e:
            raise FoodServiceException(e)

    @staticmethod
    async def get_grouped_foods_by_recipe_id(uow: IUnitOfWork, recipe_id: int) -> list[dict[str, list[str]]] | None:
        """
        Get products grouped by groups for recipe by recipe_id
        """
        try:
            async with uow:
                grouped_foods = await uow.food_repository.get_grouped_foods_by_recipe_id(recipe_id)
                return grouped_foods

        except Exception as e:
            raise FoodServiceException(e)
