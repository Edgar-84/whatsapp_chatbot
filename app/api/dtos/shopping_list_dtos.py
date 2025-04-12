from typing import Optional
from datetime import datetime

from app.lib.dto.base_dto import Base


class ShoppingListDTO(Base):
    user_id: int
    recipe_id: int
    recipe_name: str
    created_at: Optional[datetime] = None


class CreateShoppingListDTO(Base):
    user_id: int
    recipe_id: int
    recipe_name: str
