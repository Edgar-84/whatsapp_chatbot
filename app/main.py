import time
import uvicorn
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from app.routes import get_apps_router
from app.utils.unitofwork import IUnitOfWork, UnitOfWork
from app.utils.cache.ttl_cache import InMemoryUserCache
# from app.utils.cache.user_session import UserSession, UserStates
from app.wa_hooks.message_hooks import MessageClient
from app.wa_hooks.bot_menu_service import BotMenuService
from app.config.logger_settings import get_logger
from app.config.project_config import project_settings
from app.database.db import get_supabase_client
from app.services.rag_service import AskRagForRecipe


logger = get_logger("main")


def create_rag_service(supabase_client) -> AskRagForRecipe:
    logger.info("Creating [RagService]...")
    openai_key = project_settings.OPENAI_API_KEY
    return AskRagForRecipe(openai_key, supabase_client, project_settings.recipes_rag_csv_path)


def create_uow_client(supabase_client) -> IUnitOfWork:
    logger.info("Creating [UnitOfWork]...")
    return UnitOfWork(supabase_client)


def get_bot_menu_service() -> BotMenuService:
    logger.info("Creating [BotMenuService]...")
    message_client = MessageClient(
        account_sid=project_settings.account_sid,
        auth_token=project_settings.auth_token,
        twilio_number=project_settings.twilio_number
    )
    return BotMenuService(message_client)

def get_user_states() -> dict:
    logger.info("Creating [UserStates]...")
    user_states = {}  # {'phone_number': 'awaiting_id' / 'verified' / 'menu'}
    # user_states = UserStates()
    return user_states

def get_user_cache() -> dict:
    logger.info("Creating [UserCache]...")
    # user_cache = {}
    user_cache = InMemoryUserCache()
    return user_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start APP"""

    logger.info(f"Starting app ...")
    supabase_client = await get_supabase_client()
    app.state.bot_menu_service = get_bot_menu_service()
    app.state.user_states = get_user_states()
    app.state.user_cache = get_user_cache()
    app.state.uow = create_uow_client(supabase_client)
    sup_client = await supabase_client.get_client()
    app.state.rag_service = create_rag_service(sup_client)

    yield

    # Code for finish app (shutdown)
    app.state.uow = None
    app.state.rag_service = None
    logger.info("Shutting down app...")


def get_application() -> FastAPI:
    application = FastAPI(
        title="WhatsApp Chat Bot",
        debug=project_settings.DEBUG,
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 4)
        logger.info(f"PATH: {request.url.path}, METHOD: {request.method}, STATUS: {response.status_code}, "
                    f"DURATION: {process_time}ms")

        return response

    application.include_router(get_apps_router())
    return application


app = get_application()


if __name__ == "__main__":
    uvicorn.run(app="app.main:app", reload=True)
# uvicorn app.main:app --reload
