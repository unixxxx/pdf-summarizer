"""Utility functions for auth module."""

from fastapi import HTTPException, status

from ..config import Settings


def validate_oauth_provider(provider: str, settings: Settings) -> None:
    """
    Validate that the OAuth provider is supported and configured.
    
    Args:
        provider: OAuth provider name to validate
        settings: Application settings
        
    Raises:
        HTTPException: If provider is not supported or not configured
    """
    # Check if provider is supported
    if provider not in ["google", "github"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}",
        )
    
    # Check if provider is enabled
    if provider == "google" and not settings.google_oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth is not configured",
        )
    
    if provider == "github" and not settings.github_oauth_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub OAuth is not configured",
        )