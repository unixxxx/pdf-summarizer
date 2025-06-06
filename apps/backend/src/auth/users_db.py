"""Database-backed user service."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.auth.schemas import User as UserSchema
from src.auth.schemas import UserCreate
from src.database.models import User as UserModel


class UserService:
    """Database-backed user service for managing users."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update_user(self, user_data: UserCreate) -> UserSchema:
        """
        Create a new user or update existing user information.

        Args:
            user_data: User information from OAuth provider

        Returns:
            Created or updated user
        """
        try:
            # First check if user exists with this provider and provider_id
            stmt = select(UserModel).where(
                UserModel.provider == user_data.provider,
                UserModel.provider_id == user_data.provider_id,
            )
            result = await self.db.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Update existing user
                existing_user.email = user_data.email
                existing_user.name = user_data.name
                existing_user.picture = user_data.picture
                await self.db.commit()
                await self.db.refresh(existing_user)
                user = existing_user
            else:
                # Check if a user with this email already exists
                email_stmt = select(UserModel).where(UserModel.email == user_data.email)
                email_result = await self.db.execute(email_stmt)
                existing_email_user = email_result.scalar_one_or_none()
                
                if existing_email_user:
                    # Update the existing user with new provider info
                    # This allows the same email to be used with multiple providers
                    existing_email_user.name = user_data.name
                    existing_email_user.picture = user_data.picture
                    # Note: We keep the original provider info from the first sign-in
                    await self.db.commit()
                    await self.db.refresh(existing_email_user)
                    user = existing_email_user
                else:
                    # Create new user
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
        except IntegrityError:
            # Rollback the transaction if there's an integrity error
            await self.db.rollback()
            
            # Try to get the existing user by email
            email_stmt = select(UserModel).where(UserModel.email == user_data.email)
            email_result = await self.db.execute(email_stmt)
            existing_user = email_result.scalar_one_or_none()
            
            if existing_user:
                return UserSchema(
                    id=str(existing_user.id),
                    email=existing_user.email,
                    name=existing_user.name,
                    picture=existing_user.picture,
                    provider=existing_user.provider,
                    provider_id=existing_user.provider_id,
                    created_at=existing_user.created_at,
                    updated_at=existing_user.updated_at,
                )
            else:
                # Re-raise if we still can't find the user
                raise

    async def get_user(self, user_id: str) -> Optional[UserSchema]:
        """
        Get a user by ID.

        Args:
            user_id: User's unique identifier

        Returns:
            User if found, None otherwise
        """
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return None

        stmt = select(UserModel).where(UserModel.id == uuid_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

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

    async def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        """
        Get a user by email address.

        Args:
            email: User's email address

        Returns:
            User if found, None otherwise
        """
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

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

    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.

        Args:
            user_id: User's unique identifier

        Returns:
            True if user was deleted, False if not found
        """
        try:
            uuid_id = UUID(user_id)
        except ValueError:
            return False

        stmt = select(UserModel).where(UserModel.id == uuid_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

    async def get_user_count(self) -> int:
        """Get the total number of users."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(UserModel)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
