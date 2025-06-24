from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    name: str
    picture: str | None = None


class UserCreate(UserBase):
    """Schema for creating a new user from OAuth provider."""
    provider: OAuthProvider
    provider_id: str


class User(UserBase):
    """User model for API responses."""
    id: str
    provider: str
    provider_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    """Response for OAuth login initiation."""
    authorization_url: str = Field(..., description="URL to redirect user for OAuth authorization")
    state: str = Field(..., description="State parameter for CSRF protection")


