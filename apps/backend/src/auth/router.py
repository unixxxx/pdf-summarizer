"""Authentication router with OAuth2 support."""

import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer

from ..config import Settings, get_settings
from .dependencies import (
    CurrentUser,
    get_jwt_service,
    get_oauth_service,
    get_user_service,
)
from .jwt_service import JWTService
from .oauth_service import OAuthService
from .schemas import (
    MessageResponse,
    OAuthLoginResponse,
    Provider,
    ProvidersResponse,
    Token,
    User,
)
from .user_service import UserService
from .utils import validate_oauth_provider

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        400: {"description": "Bad request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
    },
)


@router.get(
    "/providers",
    response_model=ProvidersResponse,
    summary="Get available OAuth providers",
    description="Returns a list of configured OAuth providers",
)
async def get_available_providers(
    settings: Settings = Depends(get_settings)
) -> ProvidersResponse:
    """Get list of available OAuth providers."""
    providers: list[Provider] = []

    if settings.google_oauth_enabled:
        providers.append(
            Provider(
                name="google",
                display_name="Google",
                enabled=True,
                icon="google",
            )
        )

    if settings.github_oauth_enabled:
        providers.append(
            Provider(
                name="github",
                display_name="GitHub",
                enabled=True,
                icon="github",
            )
        )

    return ProvidersResponse(providers=providers)


@router.get(
    "/login/{provider}",
    response_model=OAuthLoginResponse,
    summary="Initiate OAuth login",
    description="Start the OAuth2 authentication flow for the specified provider",
    responses={
        200: {"description": "OAuth authorization URL generated"},
        400: {"description": "Invalid provider"},
    },
)
async def oauth_login(
    provider: str,
    redirect_url: Optional[str] = Query(
        None,
        description="URL to redirect after authentication",
        max_length=500,
    ),
    oauth_service: OAuthService = Depends(get_oauth_service),
    settings: Settings = Depends(get_settings),
) -> OAuthLoginResponse:
    """
    Initiate OAuth2 login flow.

    Args:
        provider: OAuth provider name ('google' or 'github')
        redirect_url: Optional URL to redirect after authentication

    Returns:
        Authorization URL and state parameter

    Raises:
        HTTPException: If provider is not supported
    """
    # Validate provider
    validate_oauth_provider(provider, settings)

    # Validate redirect URL
    redirect_url = oauth_service.validate_redirect_url(redirect_url)

    # Generate state with embedded redirect URL
    state_data = {
        "provider": provider,
        "redirect_url": redirect_url,
    }
    serializer = URLSafeSerializer(settings.session_secret_key)
    state = serializer.dumps(state_data)

    # Get authorization URL
    try:
        auth_url = await oauth_service.get_authorization_url(provider, state, redirect_url)
        return OAuthLoginResponse(authorization_url=auth_url, state=state)
    except Exception as e:
        logger.error(f"Failed to generate authorization URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth login",
        )


@router.get(
    "/callback",
    summary="OAuth callback",
    description="Handle OAuth2 callback from provider",
    responses={
        302: {"description": "Redirect to frontend with token"},
        400: {"description": "Invalid callback parameters"},
    },
)
async def oauth_callback(
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    provider: Optional[str] = Query(None, description="OAuth provider name"),
    redirect_url: Optional[str] = Query(None, description="Original redirect URL"),
    oauth_service: OAuthService = Depends(get_oauth_service),
    jwt_service: JWTService = Depends(get_jwt_service),
    user_service: UserService = Depends(get_user_service),
    settings: Settings = Depends(get_settings),
):
    """
    Handle OAuth2 callback.

    This endpoint is called by the OAuth provider after user authorization.
    It exchanges the authorization code for user information and returns a JWT token.
    """
    try:
        # Decode and validate state
        serializer = URLSafeSerializer(settings.session_secret_key)
        try:
            state_data = serializer.loads(state)
        except BadSignature:
            logger.warning("Invalid state parameter in OAuth callback")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        # Extract provider and redirect URL from state
        state_provider = state_data.get("provider", provider)
        state_redirect_url = state_data.get("redirect_url", redirect_url)

        # Get user info from OAuth provider
        user_info = await oauth_service.handle_callback(state_provider, code, state)

        # Create or update user
        user = await user_service.create_or_update_user(user_info)

        # Generate JWT token
        token = jwt_service.create_token(user)

        # Validate redirect URL
        final_redirect_url = oauth_service.validate_redirect_url(state_redirect_url)

        # Build redirect URL with token
        redirect_params = {
            "token": token.access_token,
            "user": user.name,
            "email": user.email,
        }
        # Redirect to the frontend auth callback route
        auth_callback_url = f"{final_redirect_url}/auth/callback"
        redirect_uri = f"{auth_callback_url}?{urlencode(redirect_params)}"

        logger.info(f"User {user.email} logged in via {state_provider}")
        return RedirectResponse(url=redirect_uri, status_code=status.HTTP_302_FOUND)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        
        # Redirect to error page
        error_redirect = settings.frontend_url + "/auth/error"
        error_params = {"error": "authentication_failed"}
        error_uri = f"{error_redirect}?{urlencode(error_params)}"
        
        return RedirectResponse(url=error_uri, status_code=status.HTTP_302_FOUND)


@router.get(
    "/me",
    response_model=User,
    summary="Get current user",
    description="Get information about the currently authenticated user",
    responses={
        200: {"description": "Current user information"},
        401: {"description": "Not authenticated"},
    },
)
async def get_current_user_info(
    current_user: CurrentUser,
) -> User:
    """Get current user information."""
    return current_user


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logout the current user (client should discard the token)",
    responses={
        200: {"description": "Logout successful"},
    },
)
async def logout(
    current_user: CurrentUser,
) -> MessageResponse:
    """
    Logout user.
    
    Note: This is a client-side operation. The client should discard the JWT token.
    In a more complex system, you might want to implement token blacklisting.
    """
    logger.info(f"User {current_user.email} logged out")
    return MessageResponse(message="Logout successful")


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using the current valid token",
    responses={
        200: {"description": "New token generated"},
        401: {"description": "Invalid or expired token"},
    },
)
async def refresh_token(
    current_user: CurrentUser,
    jwt_service: JWTService = Depends(get_jwt_service),
) -> Token:
    """
    Refresh access token.
    
    This endpoint allows clients to get a new token before the current one expires.
    """
    new_token = jwt_service.create_token(current_user)
    logger.info(f"Token refreshed for user {current_user.email}")
    return new_token


@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description="Delete the current user's account and all associated data",
    responses={
        204: {"description": "Account deleted successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def delete_account(
    current_user: CurrentUser,
    user_service: UserService = Depends(get_user_service),
):
    """
    Delete user account.
    
    This will permanently delete the user account and all associated data.
    This action cannot be undone.
    """
    try:
        await user_service.delete_user(current_user.id)
        logger.info(f"User account deleted: {current_user.email}")
    except Exception as e:
        logger.error(f"Failed to delete user account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account",
        )