from typing import Optional
from datetime import datetime

from app.lib.dto.base_dto import Base


class RecipeRatingsDTO(Base):
    user_id: int
    recipe_id: int
    rating: int # From 1 to 5
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


class CreateRecipeRatingDTO(Base):
    user_id: int
    recipe_id: int
    rating: int # From 1 to 5
    comment: Optional[str] = None
