from pydantic import BaseModel, EmailStr

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginInput(BaseModel):
    email: EmailStr
    password: str
