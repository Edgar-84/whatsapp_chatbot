from typing import Optional

from app.lib.dto.base_dto import Base


class RecipeUserPreferencesDTO(Base):
    meal_type: Optional[str] = None
    dietary_preference: Optional[str] = "No preference"
    include_ingredients: Optional[str] = "No preference"
    additional_notes: Optional[str] = ""
    banned_foods: Optional[list[str]] = None
    disliked_recipes_id: Optional[list[int]] = None
    disliked_recipes_comments: Optional[list[str]] = None
