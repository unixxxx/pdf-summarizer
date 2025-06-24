from urllib.parse import urlencode, urlparse

import httpx
from fastapi import HTTPException, status

from ..common.exceptions import OAuthError
from ..common.retry import retry_on_external_api
from ..config import Settings
from .schemas import OAuthProvider, UserCreate


class OAuthService:
    """Service for handling OAuth2 authentication with Google and GitHub."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def validate_oauth_provider(self, provider: OAuthProvider) -> None:
        """
        Validate that the OAuth provider is supported and configured.
        
        Args:
            provider: OAuth provider name to validate
            
        Raises:
            HTTPException: If provider is not supported or not configured
        """
        # Check if provider is supported
        if provider not in [OAuthProvider.GOOGLE, OAuthProvider.GITHUB]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}",
            )
        
        # Check if provider is enabled
        if provider == OAuthProvider.GOOGLE and not self.settings.google_oauth_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google OAuth is not configured",
            )
        
        if provider == OAuthProvider.GITHUB and not self.settings.github_oauth_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub OAuth is not configured",
            )

    def validate_redirect_url(self, redirect_url: str | None) -> str:
        """
        Validate and return the redirect URL.

        Args:
            redirect_url: URL to redirect to after authentication

        Returns:
            Validated redirect URL or default frontend URL

        Raises:
            HTTPException: If redirect URL is not allowed
        """
        if not redirect_url:
            return self.settings.frontend_url

        # Parse the URL to validate it
        parsed = urlparse(redirect_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Check if the base URL is in allowed list
        if base_url not in self.settings.allowed_redirect_urls_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Redirect URL not allowed: {base_url}",
            )

        return redirect_url

    async def get_authorization_url(
        self, provider: OAuthProvider, state: str, redirect_url: str
    ) -> str:
        """
        Get the OAuth authorization URL for a provider.

        Args:
            provider: OAuth provider name ('google' or 'github')
            state: State parameter for CSRF protection
            redirect_url: URL to redirect after authentication

        Returns:
            Authorization URL
        """
        
        # Use the base redirect URI without query parameters for OAuth providers
        # The provider and redirect_url will be encoded in the state parameter
        callback_url = self.settings.oauth_redirect_uri

        if provider == OAuthProvider.GOOGLE:
            params = {
                "client_id": self.settings.google_client_id,
                "redirect_uri": callback_url,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "offline",
                "prompt": "select_account",
            }
            return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        elif provider == OAuthProvider.GITHUB:
            params = {
                "client_id": self.settings.github_client_id,
                "redirect_uri": callback_url,
                "scope": "user:email",
                "state": state,
            }
            return f"{self.settings.github_authorize_url}?{urlencode(params)}"
        
        # This should never happen if validate_oauth_provider is called first
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )

    async def handle_callback(self, provider: OAuthProvider, code: str, state: str) -> UserCreate:
        """
        Handle OAuth callback and retrieve user information.

        Args:
            provider: OAuth provider name
            code: Authorization code from OAuth provider
            state: State parameter for CSRF validation

        Returns:
            User information from OAuth provider

        Raises:
            HTTPException: If authentication fails
        """
        try:
            if provider == OAuthProvider.GOOGLE:
                return await self._handle_google_callback(code, state)
            elif provider == OAuthProvider.GITHUB:
                return await self._handle_github_callback(code, state)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported OAuth provider: {provider}",
                )
        except httpx.HTTPError as e:
            raise OAuthError(
                provider=provider,
                detail=f"Failed to communicate with OAuth provider: {str(e)}"
            )

    @retry_on_external_api("google_oauth", max_attempts=3)
    async def _handle_google_callback(self, code: str, state: str) -> UserCreate:
        """Handle Google OAuth callback with retry."""
        # Configure timeout: 30s total, 10s connect
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Exchange code for token
            # Use the exact same redirect URI that was used in the authorization request
            token_data = {
                "code": code,
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "redirect_uri": self.settings.oauth_redirect_uri,
                "grant_type": "authorization_code",
            }

            token_response = await client.post(
                "https://oauth2.googleapis.com/token", data=token_data
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            # Get user info using the access token
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            return UserCreate(
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data.get("picture"),
                provider=OAuthProvider.GOOGLE,
                provider_id=user_data["id"],
            )

    @retry_on_external_api("github_oauth", max_attempts=3)
    async def _handle_github_callback(self, code: str, state: str) -> UserCreate:
        """Handle GitHub OAuth callback with retry."""
        # Configure timeout: 30s total, 10s connect
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Exchange code for token
            token_data = {
                "client_id": self.settings.github_client_id,
                "client_secret": self.settings.github_client_secret,
                "code": code,
                "state": state,
            }

            token_response = await client.post(
                self.settings.github_token_url,
                data=token_data,
                headers={"Accept": "application/json"},
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            if "error" in tokens:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"GitHub OAuth error: {tokens.get('error_description', tokens['error'])}",
                )

            # Get user info
            user_response = await client.get(
                self.settings.github_api_url,
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            # Get user email if not public
            email = user_data.get("email")
            if not email:
                email_response = await client.get(
                    f"{self.settings.github_api_url}/emails",
                    headers={"Authorization": f"Bearer {tokens['access_token']}"},
                )
                email_response.raise_for_status()
                emails = email_response.json()

                # Find primary email
                for email_obj in emails:
                    if email_obj.get("primary") and email_obj.get("verified"):
                        email = email_obj["email"]
                        break

                if not email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Could not retrieve email from GitHub",
                    )

            return UserCreate(
                email=email,
                name=user_data.get("name") or user_data["login"],
                picture=user_data.get("avatar_url"),
                provider=OAuthProvider.GITHUB,
                provider_id=str(user_data["id"]),
            )
