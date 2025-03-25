from app.config.logger_settings import get_logger
from app.utils.unitofwork import IUnitOfWork
from app.api.dtos.user_dtos import UserDTO
from app.api.services.service_exceptions import UserServiceException


logger = get_logger("user_service")


class UserService:
    @staticmethod
    async def get_user_by_phone_and_client_id(uow: IUnitOfWork, phone_number: str, client_id: int) -> UserDTO | None:
        try:
            async with uow:
                user = await uow.user_repository.get_user({"phone": phone_number, "client_id": client_id})
                return user

        except Exception as e:
            raise UserServiceException(e)

    @staticmethod
    async def verify_user(uow: IUnitOfWork, user_id: int) -> UserDTO:
        try:
            async with uow:
                user = await uow.user_repository.update_user({"id": user_id}, {"verified": True})
                return user

        except Exception as e:
            raise UserServiceException(e)
