from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt

from ..config import Settings
from .schemas import Token, TokenData, User


class JWTService:
    """Service for handling JWT token operations."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expiration_hours = settings.jwt_expiration_hours

    def create_access_token(self, data: dict[str, Any]) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in the token

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()

        # Set expiration
        expire = datetime.now(UTC) + timedelta(hours=self.expiration_hours)
        to_encode.update(
            {"exp": expire, "iat": datetime.now(UTC), "type": "access"}
        )

        # Create the token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> TokenData:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token to decode

        Returns:
            Decoded token data

        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode the token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Extract required fields
            sub: str = payload.get("sub")
            email: str = payload.get("email")
            name: str = payload.get("name")
            exp: int = payload.get("exp")
            iat: int = payload.get("iat")

            if not all([sub, email, name, exp, iat]):
                raise credentials_exception

            # Verify token type
            if payload.get("type") != "access":
                raise credentials_exception

            return TokenData(sub=sub, email=email, name=name, exp=exp, iat=iat)

        except JWTError:
            raise credentials_exception from None

    def create_user_token(self, user_id: str, email: str, name: str) -> str:
        """
        Create a JWT token for a user.

        Args:
            user_id: User's unique identifier
            email: User's email address
            name: User's display name

        Returns:
            JWT access token
        """
        token_data = {"sub": user_id, "email": email, "name": name}
        return self.create_access_token(token_data)

    def create_token(self, user: User) -> Token:
        """
        Create a Token response for a user.

        Args:
            user: User object

        Returns:
            Token response with access token and metadata
        """
        access_token = self.create_user_token(
            user_id=user.id,
            email=user.email,
            name=user.name
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=self.expiration_hours * 3600  # Convert hours to seconds
        )
