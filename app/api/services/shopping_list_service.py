from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.shopping_list_dtos import CreateShoppingListDTO, ShoppingListDTO
from app.api.services.service_exceptions import ShoppingListServiceException


logger = get_logger(__name__)


class ShoppingListService:
    @staticmethod
    async def create_shopping_list(uow: IUnitOfWork, shopping_list_dto: CreateShoppingListDTO) -> ShoppingListDTO:
        try:
            async with uow:
                shopping_list = await uow.shopping_list_repository.create_shopping_list(shopping_list_dto)
                return shopping_list

        except Exception as e:
            logger.warning(f"Failed to create shopping list: {e}")
            raise ShoppingListServiceException(e)

    @staticmethod
    async def get_user_shopping_lists(uow: IUnitOfWork, user_id: int) -> list[ShoppingListDTO]:
        try:
            async with uow:
                shopping_lists = await uow.shopping_list_repository.get_shopping_lists_by_user_id(user_id=user_id)
                return shopping_lists

        except Exception as e:
            logger.warning(f"Failed to get user shopping lists: {e}")
            raise ShoppingListServiceException(e)
