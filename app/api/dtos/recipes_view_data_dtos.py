from typing import Optional
from datetime import datetime

from app.lib.dto.base_dto import Base


class RecipesViewDataDTO(Base):
    id: int
    name: Optional[str] = None
    sub_title: Optional[str] = None
    preparation_method: Optional[str] = None
    nut_recommend: Optional[str] = None
    comment: Optional[str] = None
    minutes: Optional[int] = None
    meal_type: Optional[str] = None
    foods: Optional[str] = None
    ingredients: Optional[str] = None
