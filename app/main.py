import time
import uvicorn
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from app.routes import get_apps_router
from app.utils import MessageClient
from app.config.logger_settings import get_logger
from app.config.project_config import project_settings


logger = get_logger("main")
# app = FastAPI()



def get_message_client() -> MessageClient:
    logger.info("Creating [MessageClient]...")
    return MessageClient(
        account_sid=project_settings.account_sid,
        auth_token=project_settings.auth_token,
        twilio_number=project_settings.twilio_number
    )

def get_user_states() -> dict:
    logger.info("Creating [UserStates]...")
    user_states = {}  # {'phone_number': 'awaiting_id' / 'verified' / 'menu'}
    return user_states

def get_validated_users() -> set:
    logger.info("Creating [ValidatedUsers]...")
    validated_users = set()
    return validated_users

def get_valid_client_ids() -> set:
    logger.info("Creating [ValidClientIds]...")
    valid_client_ids = {"111", "222", "333"}
    return valid_client_ids

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start APP"""

    logger.info(f"Starting app ...")
    app.state.message_client = get_message_client()
    app.state.user_states = get_user_states()
    app.state.validated_users = get_validated_users()
    app.state.valid_client_ids = get_valid_client_ids()
    # Initialize UOW
    # supabase_client = get_supabase_client()
    # uow = UnitOfWork(supabase_client)
    # app.state.uow = uow

    yield

    # Code for finish app (shutdown)
    app.state.uow = None
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
