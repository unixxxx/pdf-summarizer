"""User domain service following DDD principles."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import DuplicateResourceError, NotFoundError
from ..database.models import User as UserModel
from .schemas import User as UserSchema
from .schemas import UserCreate

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user lifecycle following DDD principles."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_or_update_user(self, user_data: UserCreate) -> UserSchema:
        """
        Create a new user or update existing user information.

        This method handles OAuth login flow where users can sign in with
        different providers but should map to the same user account.

        Args:
            user_data: User information from OAuth provider

        Returns:
            Created or updated user

        Raises:
            IntegrityError: If there's a database constraint violation
        """
        # Check if user exists with this provider
        existing_user = await self._find_by_provider(
            provider=user_data.provider,
            provider_id=user_data.provider_id
        )

        if existing_user:
            # Update existing user info
            return await self._update_user(existing_user, user_data)

        # Check if user with this email exists (different provider)
        existing_user = await self._find_by_email(user_data.email)
        
        if existing_user:
            logger.info(
                f"User with email {user_data.email} exists with different provider. "
                f"Keeping original provider: {existing_user.provider}"
            )
            # Update user info but keep original provider
            return await self._update_user(existing_user, user_data, keep_provider=True)

        # Create new user
        return await self._create_user(user_data)

    async def get_user(self, user_id: str) -> UserSchema:
        """
        Get a user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User

        Raises:
            NotFoundError: If user not found
        """
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            raise NotFoundError(f"Invalid user ID format: {user_id}")

        stmt = select(UserModel).where(UserModel.id == uuid_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")

        return self._model_to_schema(user)

    async def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        """
        Get a user by email address.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        user = await self._find_by_email(email)
        return self._model_to_schema(user) if user else None

    async def delete_user(self, user_id: str) -> None:
        """
        Delete a user and all associated data.

        Args:
            user_id: User's unique identifier

        Raises:
            NotFoundError: If user not found
        """
        await self.get_user(user_id)  # This will raise NotFoundError if not found
        
        try:
            uuid_id = UUID(user_id)
            stmt = select(UserModel).where(UserModel.id == uuid_id)
            result = await self.db.execute(stmt)
            user_model = result.scalar_one()
            
            await self.db.delete(user_model)
            await self.db.commit()
            
            logger.info(f"Deleted user {user_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise

    async def get_user_count(self) -> int:
        """Get the total number of users."""
        stmt = select(func.count()).select_from(UserModel)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def list_users(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> list[UserSchema]:
        """
        List users with pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of users
        """
        stmt = (
            select(UserModel)
            .order_by(UserModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        return [self._model_to_schema(user) for user in users]

    # Private helper methods

    async def _find_by_provider(
        self, 
        provider: str, 
        provider_id: str
    ) -> Optional[UserModel]:
        """Find user by provider and provider ID."""
        stmt = select(UserModel).where(
            UserModel.provider == provider,
            UserModel.provider_id == provider_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_by_email(self, email: str) -> Optional[UserModel]:
        """Find user by email."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_user(self, user_data: UserCreate) -> UserSchema:
        """Create a new user."""
        try:
            user = UserModel(
                email=user_data.email,
                name=user_data.name,
                picture=user_data.picture,
                provider=user_data.provider,
                provider_id=user_data.provider_id,
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Created new user: {user.email}")
            return self._model_to_schema(user)
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise DuplicateResourceError("User", user_data.email)

    async def _update_user(
        self, 
        user: UserModel, 
        user_data: UserCreate,
        keep_provider: bool = False
    ) -> UserSchema:
        """Update existing user."""
        try:
            # Always update these fields
            user.email = user_data.email
            user.name = user_data.name
            user.picture = user_data.picture
            
            # Only update provider info if not keeping original
            if not keep_provider:
                user.provider = user_data.provider
                user.provider_id = user_data.provider_id
            
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Updated user: {user.email}")
            return self._model_to_schema(user)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user: {str(e)}")
            raise

    def _model_to_schema(self, user: UserModel) -> UserSchema:
        """Convert database model to schema."""
        return UserSchema(
            id=str(user.id),
            email=user.email,
            name=user.name,
            picture=user.picture,
            provider=user.provider,
            provider_id=user.provider_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )