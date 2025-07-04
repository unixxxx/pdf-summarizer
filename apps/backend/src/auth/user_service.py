"""Refactored user domain service without session storage."""

import logging
from uuid import UUID

from shared.models import User as UserModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import ConflictException, NotFoundException
from .schemas import User as UserSchema
from .schemas import UserCreate

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user lifecycle - refactored without session storage."""

    async def create_or_update_user(
        self, 
        db: AsyncSession,
        user_data: UserCreate
    ) -> UserSchema:
        """
        Create a new user or update existing user information.

        This method handles OAuth login flow where users can sign in with
        different providers but should map to the same user account.

        Args:
            db: Database session
            user_data: User information from OAuth provider

        Returns:
            Created or updated user

        Raises:
            IntegrityError: If there's a database constraint violation
        """
        # Check if user exists with this provider
        existing_user = await self._find_by_provider(
            db=db,
            provider=user_data.provider,
            provider_id=user_data.provider_id
        )

        if existing_user:
            # Update existing user info
            return await self._update_user(db, existing_user, user_data)

        # Check if user with this email exists (different provider)
        existing_user = await self._find_by_email(db, user_data.email)
        
        if existing_user:
            logger.info(
                f"User with email {user_data.email} exists with different provider. "
                f"Keeping original provider: {existing_user.provider}"
            )
            # Update user info but keep original provider
            return await self._update_user(db, existing_user, user_data, keep_provider=True)

        # Create new user
        return await self._create_user(db, user_data)

    async def get_user(self, db: AsyncSession, user_id: str) -> UserSchema:
        """
        Get a user by ID.

        Args:
            db: Database session
            user_id: User's unique identifier

        Returns:
            User

        Raises:
            NotFoundException: If user not found
        """
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            raise NotFoundException(f"Invalid user ID format: {user_id}")

        stmt = select(UserModel).where(UserModel.id == uuid_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")

        return self._model_to_schema(user)

    async def get_user_by_email(
        self, 
        db: AsyncSession,
        email: str
    ) -> UserSchema | None:
        """
        Get a user by email address.

        Args:
            db: Database session
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        user = await self._find_by_email(db, email)
        return self._model_to_schema(user) if user else None

    async def get_user_by_provider(
        self,
        db: AsyncSession,
        provider: str,
        provider_id: str
    ) -> UserSchema | None:
        """
        Get a user by provider information.

        Args:
            db: Database session
            provider: OAuth provider name
            provider_id: User's ID from the provider

        Returns:
            User if found, None otherwise
        """
        user = await self._find_by_provider(db, provider, provider_id)
        return self._model_to_schema(user) if user else None

    async def delete_user(self, db: AsyncSession, user_id: str) -> None:
        """
        Delete a user and all associated data.

        Args:
            db: Database session
            user_id: User's unique identifier

        Raises:
            NotFoundException: If user not found
        """
        await self.get_user(db, user_id)  # This will raise NotFoundException if not found
        
        try:
            uuid_id = UUID(user_id)
            stmt = select(UserModel).where(UserModel.id == uuid_id)
            result = await db.execute(stmt)
            user_model = result.scalar_one()
            
            await db.delete(user_model)
            await db.commit()
            
            logger.info(f"Deleted user {user_id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise

    async def get_user_count(self, db: AsyncSession) -> int:
        """Get the total number of users."""
        stmt = select(func.count()).select_from(UserModel)
        result = await db.execute(stmt)
        return result.scalar() or 0

    async def list_users(
        self,
        db: AsyncSession,
        limit: int = 100, 
        offset: int = 0
    ) -> list[UserSchema]:
        """
        List users with pagination.

        Args:
            db: Database session
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
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        return [self._model_to_schema(user) for user in users]

    async def _find_by_provider(
        self,
        db: AsyncSession,
        provider: str,
        provider_id: str
    ) -> UserModel | None:
        """Find user by provider details."""
        stmt = select(UserModel).where(
            UserModel.provider == provider,
            UserModel.provider_id == provider_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_by_email(
        self,
        db: AsyncSession,
        email: str
    ) -> UserModel | None:
        """Find user by email (case-insensitive)."""
        stmt = select(UserModel).where(
            func.lower(UserModel.email) == func.lower(email)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_user(
        self,
        db: AsyncSession,
        user_data: UserCreate
    ) -> UserSchema:
        """Create a new user."""
        user = UserModel(
            email=user_data.email,
            name=user_data.name,
            picture=user_data.picture,
            provider=user_data.provider,
            provider_id=user_data.provider_id,
        )

        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Created new user: {user.email} via {user.provider}")
            return self._model_to_schema(user)
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Failed to create user: {e}")
            
            # Check if it's a duplicate email
            if "email" in str(e):
                raise ConflictException(
                    f"User with email {user_data.email} already exists"
                )
            raise

    async def _update_user(
        self,
        db: AsyncSession,
        user: UserModel,
        user_data: UserCreate,
        keep_provider: bool = False
    ) -> UserSchema:
        """Update existing user information."""
        # Update fields
        user.name = user_data.name
        user.picture = user_data.picture
        user.last_login = func.now()

        # Only update provider info if not keeping original
        if not keep_provider:
            user.provider = user_data.provider
            user.provider_id = user_data.provider_id

        try:
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"Updated user: {user.email}")
            return self._model_to_schema(user)
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Failed to update user: {e}")
            raise

    def _model_to_schema(self, user: UserModel) -> UserSchema:
        """Convert database model to Pydantic schema."""
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