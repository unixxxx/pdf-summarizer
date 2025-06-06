from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None


class UserCreate(UserBase):
    provider: str
    provider_id: str


class User(UserBase):
    id: str
    provider: str
    provider_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    sub: str
    email: str
    name: str
    exp: int
    iat: int


class OAuthLoginResponse(BaseModel):
    authorization_url: str
    state: str
