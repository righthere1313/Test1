from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    teaching_subject: Optional[str] = None
    teaching_style: Optional[str] = None
    additional_info: Optional[str] = None

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teaching_subject: Optional[str] = None
    teaching_style: Optional[str] = None
