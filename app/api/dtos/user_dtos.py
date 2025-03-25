from typing import Optional
from datetime import datetime

from app.lib.dto.base_dto import Base


class UserDTO(Base):
    id: int
    client_id: int
    phone: str
    verified: bool
    pdf_result_link: Optional[str] = None
    ascii_result_link: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
