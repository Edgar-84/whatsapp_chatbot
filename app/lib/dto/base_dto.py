from pydantic import BaseModel


class Base(BaseModel):
    """
    Base DTO Pydantic with 'from_attributes' for ORM
    """
    class Config:
        from_attributes = True
