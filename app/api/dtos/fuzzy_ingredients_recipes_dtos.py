from typing import Optional

from app.lib.dto.base_dto import Base


class FuzzyIngredientsRecipesDTO(Base):
    id: int
    ingredient_he: str
    ingredient_en: Optional[str]
    recipe_id_list: list[int]
