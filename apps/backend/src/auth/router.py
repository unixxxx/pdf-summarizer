from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer

from src.auth.dependencies import (
    CurrentUser,
    get_jwt_service,
    get_oauth_service,
    get_user_service,
)
from src.auth.jwt import JWTService
from src.auth.oauth import OAuthService
from src.auth.schemas import OAuthLoginResponse, Token, User
from src.auth.users import UserService
from src.config import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/providers")
async def get_available_providers(settings: Settings = Depends(get_settings)):
    """Get list of available OAuth providers."""
    providers = []

    if settings.google_oauth_enabled:
        providers.append({"name": "google", "display_name": "Google", "enabled": True})

    if settings.github_oauth_enabled:
        providers.append({"name": "github", "display_name": "GitHub", "enabled": True})

    return {"providers": providers}


@router.get("/login/{provider}", response_model=OAuthLoginResponse)
async def oauth_login(
    provider: str,
    redirect_url: Optional[str] = Query(
        None, description="URL to redirect after authentication"
    ),
    oauth_service: OAuthService = Depends(get_oauth_service),
    settings: Settings = Depends(get_settings),
):
    """
    Initiate OAuth2 login flow.

    Args:
        provider: OAuth provider name ('google' or 'github')
        redirect_url: Optional URL to redirect after authentication

    Returns:
        Authorization URL and state parameter
    """
    # Validate redirect URL
    redirect_url = oauth_service.validate_redirect_url(redirect_url)

    # Generate state with embedded redirect URL
    state_data = {"provider": provider, "redirect_url": redirect_url}
    serializer = URLSafeSerializer(settings.session_secret_key)
    state = serializer.dumps(state_data)

    # Get authorization URL
    auth_url = await oauth_service.get_authorization_url(provider, state, redirect_url)

    return OAuthLoginResponse(authorization_url=auth_url, state=state)


@router.get("/callback")
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

    Args:
        code: Authorization code from OAuth provider
        state: State parameter for CSRF validation
        provider: OAuth provider name
        redirect_url: URL to redirect after authentication

    Returns:
        Redirect to frontend with JWT token
    """
    try:
        # Decode and validate state
        serializer = URLSafeSerializer(settings.session_secret_key)
        try:
            state_data = serializer.loads(state)

            # Extract provider from state if not in query params
            if not provider:
                provider = state_data.get("provider")
                if not provider:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Provider not found in state parameter",
                    )

            # Validate provider matches if both are present
            elif state_data.get("provider") != provider:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Provider mismatch in state parameter",
                )

            # Use redirect URL from state if not provided
            if not redirect_url:
                redirect_url = state_data.get("redirect_url", settings.frontend_url)

        except BadSignature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        # Handle OAuth callback
        user_data = await oauth_service.handle_callback(provider, code, state)

        # Create or update user
        user = await user_service.create_or_update_user(user_data)

        # Generate JWT token
        token = jwt_service.create_user_token(
            user_id=user.id, email=user.email, name=user.name
        )

        # Redirect to frontend with token
        redirect_params = {"token": token, "provider": provider}

        # Add query parameters to redirect URL
        separator = "&" if "?" in redirect_url else "?"
        final_redirect_url = f"{redirect_url}{separator}{urlencode(redirect_params)}"

        return RedirectResponse(
            url=final_redirect_url, status_code=status.HTTP_302_FOUND
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log the error in production
        print(f"OAuth callback error: {str(e)}")

        # Redirect to frontend with error
        error_params = {"error": "authentication_failed", "message": str(e)}
        separator = "&" if "?" in redirect_url else "?"
        error_redirect_url = f"{redirect_url}{separator}{urlencode(error_params)}"

        return RedirectResponse(
            url=error_redirect_url, status_code=status.HTTP_302_FOUND
        )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: CurrentUser,
    settings: Settings = Depends(get_settings),
):
    """
    Logout the current user.

    This is a placeholder for session-based logout.
    With JWT tokens, the client should simply discard the token.

    Returns:
        Success message
    """
    # In a session-based system, we would clear the session here
    # With JWT, the client is responsible for discarding the token

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current user information.

    Requires authentication.

    Returns:
        Current user information
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: CurrentUser,
    jwt_service: JWTService = Depends(get_jwt_service),
    settings: Settings = Depends(get_settings),
):
    """
    Refresh the JWT token.

    Requires authentication.

    Returns:
        New JWT token
    """
    # Generate new token
    new_token = jwt_service.create_user_token(
        user_id=current_user.id, email=current_user.email, name=current_user.name
    )

    return Token(
        access_token=new_token, expires_in=settings.jwt_expiration_hours * 3600
    )


@router.delete("/me")
async def delete_current_user(
    current_user: CurrentUser, user_service: UserService = Depends(get_user_service)
):
    """
    Delete the current user account.

    Requires authentication.

    Returns:
        Success message
    """
    # Delete user
    deleted = await user_service.delete_user(current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )

    return {"message": "User account deleted successfully"}
