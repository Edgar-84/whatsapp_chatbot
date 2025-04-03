from typing import Optional

from app.lib.dto.base_dto import Base


class MealTypeDTO(Base):
    id: int
    name: str
    menu_name: Optional[str] = None
