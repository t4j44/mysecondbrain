"""
AI Content Engine FastAPI Router
Module Owner: Agent 9
Endpoints: /api/v1/content
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.content import ContentRepository
from app.schemas.content import (
    ContentCreateRequest,
    ContentGenerateRequest,
    ContentListResponse,
    ContentResponse,
    ContentUpdateRequest,
    ContentVersionListResponse,
)
from app.services.content.content_service import ContentService

router = APIRouter()


async def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


def get_content_service() -> ContentService:
    class MockDbClient:
        pass

    return ContentService(repo=ContentRepository(db_client=MockDbClient()))


def build_meta() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "v1",
        "module": "ai-content-engine",
    }


@router.get("", response_model=ContentListResponse, status_code=status.HTTP_200_OK)
async def list_content_items(
    content_type: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """List generated content updates and drafts."""
    items = await service.list_content(user_id, content_type, status_filter, limit, offset)
    return {
        "data": items,
        "pagination": {"limit": limit, "offset": offset, "total": len(items)},
        "meta": build_meta(),
    }


@router.post("/generate", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def generate_content(
    payload: ContentGenerateRequest,
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """
    Generate authentic professional updates grounded in selected Second Brain memories.
    Enforces DRAFT state and executes claim validation.
    """
    # Mock retrieving source records based on selected UUIDs
    mock_sources = [
        {
            "id": uid,
            "title": f"Source #{idx + 1}",
            "excerpt": "Verified founder operation execution note.",
        }
        for idx, uid in enumerate(payload.source_record_ids)
    ]
    created = await service.generate_grounded_content(user_id, payload.model_dump(), mock_sources)
    return {"data": created, "meta": build_meta()}


@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content_draft(
    payload: ContentCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """Manually create a content item draft."""
    created = await service.create_content_draft(user_id, payload.model_dump())
    return {"data": created, "meta": build_meta()}


@router.get("/{id}", response_model=ContentResponse, status_code=status.HTTP_200_OK)
async def get_content(
    id: str,
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """Retrieve specific content item by UUID."""
    item = await service.get_content(user_id, id)
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found or unauthorized.")
    return {"data": item, "meta": build_meta()}


@router.patch("/{id}", response_model=ContentResponse, status_code=status.HTTP_200_OK)
async def update_content(
    id: str,
    payload: ContentUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """Update content draft or approve for publishing."""
    updated = await service.update_content(user_id, id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Content item not found or unauthorized.")
    return {"data": updated, "meta": build_meta()}


@router.get(
    "/{id}/versions", response_model=ContentVersionListResponse, status_code=status.HTTP_200_OK
)
async def list_content_versions(
    id: str,
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """Retrieve immutable historical versions and snapshots for a content item."""
    versions = await service.list_versions(user_id, id)
    return {"data": versions, "meta": build_meta()}


@router.post(
    "/{id}/versions/{version_id}/restore",
    response_model=ContentResponse,
    status_code=status.HTTP_200_OK,
)
async def restore_content_version(
    id: str,
    version_id: int,
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """Restore content item to a specific historical snapshot without erasing intervention history."""
    restored = await service.restore_version(user_id, id, version_id)
    if not restored:
        raise HTTPException(status_code=404, detail="Version snapshot or content item not found.")
    return {"data": restored, "meta": build_meta()}


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    id: str,
    user_id: str = Depends(get_current_user_id),
    service: ContentService = Depends(get_content_service),
):
    """Soft-delete a content item."""
    success = await service.repo.delete_content(user_id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Content item not found or unauthorized.")
    return None
