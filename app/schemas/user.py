from typing import Optional
from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    OWNER = "OWNER"
    SUPERADMIN = "SUPERADMIN"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    is_active: Optional[bool] = None

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    profile_picture: Optional[str] = None

    class Config:
        orm_mode = True
