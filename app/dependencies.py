from enum import Enum
from typing import Annotated
from fastapi import Depends, Request
from app.utils.unitofwork import IUnitOfWork 
from app.utils.cache.ttl_cache import InMemoryUserCache
from app.wa_hooks.bot_menu_service import BotMenuService
from app.config.logger_settings import get_logger
from app.services.rag_service import AskRagForRecipe


logger = get_logger("dependencies")


def get_user_states(request: Request) -> dict:
    return request.app.state.user_states


def get_bot_menu_service(request: Request) -> BotMenuService:
    return request.app.state.bot_menu_service


def get_unit_of_work(request: Request) -> IUnitOfWork:
    return request.app.state.uow

def get_user_cache(request: Request) -> InMemoryUserCache:
    return request.app.state.user_cache


def get_rag_service(request: Request) -> AskRagForRecipe:
    return request.app.state.rag_service


BotMenuServiceDep = Annotated[BotMenuService, Depends(get_bot_menu_service)]
UserStatesDep = Annotated[dict, Depends(get_user_states)]
UserCacheDep = Annotated[InMemoryUserCache, Depends(get_user_cache)]
UOWDep = Annotated[IUnitOfWork, Depends(get_unit_of_work)]
AskRagForRecipeDep = Annotated[AskRagForRecipe, Depends(get_rag_service)]
