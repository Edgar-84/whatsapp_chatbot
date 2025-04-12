from enum import Enum
from typing import Annotated
from fastapi import Depends, Request
from app.utils.unitofwork import IUnitOfWork 
from app.wa_hooks.bot_menu_service import BotMenuService
from app.config.logger_settings import get_logger
from app.services.rag_service import AskRagForRecipe


logger = get_logger("dependencies")


class UserStates(str, Enum):
    AWAITING_VERIFICATION = "awaiting_verification"  # Waiting for verification
    MAIN_MENU = "main_menu"  # Main menu
    MY_RESULT_MENU = "my_result_menu"  # View My Results
    MY_RESTRICTIONS_MENU = "my_restrictions_menu"  # See My Restrictions

    ASK_USER_WHANT_RECIPES = "ask_user_whant_recipes"  # Ask user want recipes
    CHOICE_MEAL_TYPE_MENU = "choice_meal_type_menu"  # After choose Meal Type
    DIETARY_PREFERENCE_FILTER = "dietary_preference_filter"  # Dietary Preference Filter
    INCLUDE_INGREDIENTS_FILTER = "include_ingredients_filter"  # Include Ingredients Filter
    USER_WAITING_ANSWER = "user_waiting_answer"  # Set User to Waiting answer state
    SHOW_PERSONALIZED_RECIPES_MENU = "show_personalized_recipes_menu"  # When return fit recipes
    ASK_WHY_DISLIKE = "ask_why_dislike"  # Ask user why dislike
    MENU_SAVE_RECIPE = "menu_save_recipe"  # Menu to save recipe

    NUTRITION_ASSISTANT_MENU = "nutrition_assistant_menu"  # Personal Nutrition Assistant


def get_user_states(request: Request) -> dict:
    return request.app.state.user_states


def get_bot_menu_service(request: Request) -> BotMenuService:
    return request.app.state.bot_menu_service


def get_unit_of_work(request: Request) -> IUnitOfWork:
    return request.app.state.uow

def get_user_cache(request: Request) -> dict:
    return request.app.state.user_cache


def get_rag_service(request: Request) -> AskRagForRecipe:
    return request.app.state.rag_service


BotMenuServiceDep = Annotated[BotMenuService, Depends(get_bot_menu_service)]
UserStatesDep = Annotated[dict, Depends(get_user_states)]
UserCacheDep = Annotated[dict, Depends(get_user_cache)]
UOWDep = Annotated[IUnitOfWork, Depends(get_unit_of_work)]
AskRagForRecipeDep = Annotated[AskRagForRecipe, Depends(get_rag_service)]
