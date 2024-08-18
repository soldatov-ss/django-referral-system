from pydantic import BaseModel


class BaseModelDTO(BaseModel):
    class Config:
        populate_by_name = True
