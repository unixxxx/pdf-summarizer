"""Dependencies for Quiz domain."""

from typing import Annotated

from fastapi import Depends

from .async_service import AsyncQuizService


def get_async_quiz_service() -> AsyncQuizService:
    """Get async quiz service instance."""
    return AsyncQuizService()


AsyncQuizServiceDep = Annotated[AsyncQuizService, Depends(get_async_quiz_service)]