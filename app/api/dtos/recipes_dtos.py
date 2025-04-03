from typing import Optional
from app.lib.dto.base_dto import Base


class RecipeDTO(Base):
    id: int
    name: str
    sub_id: int = 0
    difficulty_level: int
    kosher_type: int
    preparation_time: int
    preparation_method: str
    main_picture_url: str
    nutrifox_recipe_id: int
    create_at: int
    status: int
    sub_title: Optional[str] = None
    portion_num: Optional[int] = None
    nut_recommend: Optional[str] = None
    comment: Optional[str] = None
    main_picture: Optional[str] = None
    secondary_picture: Optional[str] = None
    nutrition_picture: Optional[str] = None
    calories_val: Optional[float] = None
    sodium_val: Optional[float] = None
    fat_val: Optional[float] = None
    protein_val: Optional[float] = None
    carbs_val: Optional[float] = None
    fiber_val: Optional[float] = None
    original_recipe: Optional[str] = None
    referral_id: Optional[int] = None
    clients_only: int = 0