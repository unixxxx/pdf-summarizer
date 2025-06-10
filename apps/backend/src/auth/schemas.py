from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    name: str
    picture: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user from OAuth provider."""
    provider: str
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


class Provider(BaseModel):
    """OAuth provider information."""
    name: str = Field(..., description="Provider identifier")
    display_name: str = Field(..., description="Human-readable provider name")
    enabled: bool = Field(..., description="Whether provider is enabled")
    icon: Optional[str] = Field(None, description="Icon identifier for UI")


class ProvidersResponse(BaseModel):
    """Response containing available OAuth providers."""
    providers: list[Provider] = Field(..., description="List of available OAuth providers")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str = Field(..., description="Response message")
