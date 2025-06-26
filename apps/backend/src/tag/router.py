from fastapi import APIRouter, Depends

from ..auth.dependencies import CurrentUserDep
from ..database.session import get_db
from .dependencies import CachedTagServiceDep
from .schemas import TagResponse

router = APIRouter(prefix="/tag", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def get_tags(
    cached_tag_service: CachedTagServiceDep,
    _: CurrentUserDep,  # Authentication check only
    db = Depends(get_db),
) -> list[TagResponse]:
    """
    Get all available tags for suggestions.
    """
    return await cached_tag_service.get_all_tags(db)




