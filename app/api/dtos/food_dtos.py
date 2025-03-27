from typing import Optional

from app.lib.dto.base_dto import Base


class FoodDTO(Base):
    id: int
    name: str
    lab_code: str
    food_group_id: int
    usda: Optional[int] = None
    energy: Optional[int] = None
    protein: Optional[float] = None
    total_lipid: Optional[float] = None
    carbohydrate: Optional[float] = None
    fiber: Optional[float] = None
    calcium: Optional[float] = None
    iron: Optional[float] = None
    magnesium: Optional[float] = None
    zinc: Optional[float] = None
    sodium: Optional[float] = None
    vitamin_c: Optional[float] = None
    vitamin_b6: Optional[float] = None
    folate: Optional[float] = None
    vitamin_b12: Optional[float] = None
    vitamin_e: Optional[float] = None
    vitamin_d: Optional[float] = None
    vitamin_a: Optional[float] = None
    omega3: Optional[float] = None
    portion: int = 0
