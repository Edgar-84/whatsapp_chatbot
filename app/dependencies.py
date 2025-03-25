from enum import Enum
from typing import Annotated
from fastapi import Depends, Request
from app.utils.unitofwork import IUnitOfWork 
from app.wa_hooks.bot_menu_service import BotMenuService
from app.config.logger_settings import get_logger


logger = get_logger("dependencies")


class UserStates(str, Enum):
    AWAITING_VERIFICATION = "awaiting_verification"  # Waiting for verification
    MAIN_MENU = "main_menu"  # Main menu
    MY_RESULT_MENU = "my_result_menu"  # View My Results
    MY_RESTRICTIONS_MENU = "my_restrictions_menu"  # See My Restrictions
    PERSONALIZED_RECIPES_MENU = "personalized_recipes_menu"  # Personalized Recipes
    NUTRITION_ASSISTANT_MENU = "nutrition_assistant_menu"  # Personal Nutrition Assistant


def get_user_states(request: Request) -> dict:
    return request.app.state.user_states


def get_bot_menu_service(request: Request) -> BotMenuService:
    return request.app.state.bot_menu_service


def get_unit_of_work(request: Request) -> IUnitOfWork:
    return request.app.state.uow

def get_user_cache(request: Request) -> dict:
    return request.app.state.user_cache


BotMenuServiceDep = Annotated[BotMenuService, Depends(get_bot_menu_service)]
UserStatesDep = Annotated[dict, Depends(get_user_states)]
UserCacheDep = Annotated[dict, Depends(get_user_cache)]
UOWDep = Annotated[IUnitOfWork, Depends(get_unit_of_work)]
