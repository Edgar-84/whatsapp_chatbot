from typing import Annotated
from fastapi import Depends, Request
from app.config.project_config import project_settings
from app.utils import MessageClient
from app.config.logger_settings import get_logger


logger = get_logger("dependencies")

# from app.utils.unitofwork import IUnitOfWork 

# def get_unit_of_work(client: SupabaseClient = Depends(get_supabase_client)) -> IUnitOfWork:
#     return UnitOfWork(client)


# def get_unit_of_work(request: Request) -> IUnitOfWork:
#     return request.app.state.uow


# UOWDep = Annotated[IUnitOfWork, Depends(get_unit_of_work)]


def get_user_states(request: Request) -> dict:
    return request.app.state.user_states


def get_validated_users(request: Request) -> set:
    return request.app.state.validated_users


def get_valid_client_ids(request: Request) -> set:
    return request.app.state.valid_client_ids


def get_message_client(request: Request) -> MessageClient:
    return request.app.state.message_client

MessageClientDep = Annotated[MessageClient, Depends(get_message_client)]
UserStatesDep = Annotated[dict, Depends(get_user_states)]
ValidatedUsersDep = Annotated[set, Depends(get_validated_users)]
ValidClientIdsDep = Annotated[set, Depends(get_valid_client_ids)]
