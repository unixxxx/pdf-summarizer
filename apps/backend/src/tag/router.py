from uuid import UUID

from fastapi import APIRouter, Depends

from ..auth.dependencies import CurrentUserDep
from ..database.session import get_db
from .dependencies import TagServiceDep
from .schemas import TagGenerationRequest, TagResponse

router = APIRouter(prefix="/tag", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def get_tags(
    tag_service: TagServiceDep,
    db = Depends(get_db),
) -> list[TagResponse]:
    """
    Get all available tags for the current user.
    """
    tags_with_counts = await tag_service.get_all_tags_with_counts(db)
    
    return [
        TagResponse(
            id=tag_data["id"],
            name=tag_data["name"],
            slug=tag_data["slug"],
            color=tag_data["color"],
            document_count=tag_data["document_count"],
        )
        for tag_data in tags_with_counts
    ]


@router.post("/generate", response_model=list[TagResponse])
async def generate_tags(
    request: TagGenerationRequest,
    tag_service: TagServiceDep,
    current_user: CurrentUserDep,
    db = Depends(get_db),
) -> list[TagResponse]:
    """
    Generate tags for a summary using AI.
    """
    tags = await tag_service.generate_tags_for_summary(
        request.summary_id, current_user.id, db
    )
    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            slug=tag.slug,
            color=tag.color,
            document_count=1,  # New tag has 1 document
        )
        for tag in tags
    ]


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    name: str,
    tag_service: TagServiceDep,
    current_user: CurrentUserDep,
    db = Depends(get_db),
) -> TagResponse:
    """
    Update a tag's name.
    """
    tag = await tag_service.update_tag(tag_id, name, current_user.id, db)
    return TagResponse(
        id=tag.id,
        name=tag.name,
        slug=tag.slug,
        color=tag.color,
        document_count=1,  # Would need to fetch actual count
    )


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: UUID,
    tag_service: TagServiceDep,
    current_user: CurrentUserDep,
    db = Depends(get_db),
) -> dict:
    """
    Delete a tag.
    """
    await tag_service.delete_tag(tag_id, current_user.id, db)
    return {"message": "Tag deleted successfully"}