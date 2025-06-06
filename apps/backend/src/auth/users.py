import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from src.auth.schemas import User, UserCreate


class UserService:
    """
    Simple in-memory user service for managing users.
    In production, this would be replaced with a database.
    """

    def __init__(self):
        # In-memory storage for users
        # Key: user_id, Value: User dict
        self._users: Dict[str, Dict] = {}

        # Index for finding users by provider
        # Key: (provider, provider_id), Value: user_id
        self._provider_index: Dict[tuple, str] = {}

    async def create_or_update_user(self, user_data: UserCreate) -> User:
        """
        Create a new user or update existing user information.

        Args:
            user_data: User information from OAuth provider

        Returns:
            Created or updated user
        """
        # Check if user already exists
        provider_key = (user_data.provider, user_data.provider_id)
        existing_user_id = self._provider_index.get(provider_key)

        if existing_user_id:
            # Update existing user
            user = self._users[existing_user_id]
            user.update(
                {
                    "email": user_data.email,
                    "name": user_data.name,
                    "picture": user_data.picture,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "email": user_data.email,
                "name": user_data.name,
                "picture": user_data.picture,
                "provider": user_data.provider,
                "provider_id": user_data.provider_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            # Store user
            self._users[user_id] = user
            self._provider_index[provider_key] = user_id

        return User(**user)

    async def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User if found, None otherwise
        """
        user_data = self._users.get(user_id)
        return User(**user_data) if user_data else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email address.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        for user_data in self._users.values():
            if user_data["email"] == email:
                return User(**user_data)
        return None

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: User's unique identifier

        Returns:
            True if user was deleted, False if not found
        """
        user_data = self._users.get(user_id)
        if not user_data:
            return False

        # Remove from provider index
        provider_key = (user_data["provider"], user_data["provider_id"])
        self._provider_index.pop(provider_key, None)

        # Remove user
        del self._users[user_id]

        return True

    def get_user_count(self) -> int:
        """Get the total number of users."""
        return len(self._users)
