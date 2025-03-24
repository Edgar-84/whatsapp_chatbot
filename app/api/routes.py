from fastapi import APIRouter
from app.api.controllers import base_controller


base_router = APIRouter()
base_router.include_router(base_controller.router)
