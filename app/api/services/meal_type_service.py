from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.meal_type_dtos import MealTypeDTO
from app.api.services.service_exceptions import MealTypeServiceException


logger = get_logger(__name__)


class MealTypeService:
    @staticmethod
    async def get_all_meal_types(uow: IUnitOfWork) -> list[MealTypeDTO]:
        try:
            async with uow:
                meal_types = await uow.meal_type_repository.get_all_meal_types()
                return meal_types

        except Exception as e:
            raise MealTypeServiceException(e)
