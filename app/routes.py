from fastapi import APIRouter

from app.api.routes import base_router


def get_apps_router():
    router = APIRouter()
    router.include_router(base_router)
    return router
