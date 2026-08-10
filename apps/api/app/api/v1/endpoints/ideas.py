"""
Idea Vault FastAPI Router
Module Owner: Agent 9
Endpoints: /api/v1/ideas
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.ideas import IdeaRepository
from app.schemas.idea import (
    IdeaConversionResponse,
    IdeaCreateRequest,
    IdeaListResponse,
    IdeaResponse,
    IdeaToProjectConvertRequest,
    IdeaUpdateRequest,
)
from app.services.ideas.idea_service import IdeaService

router = APIRouter()


# Dependency abstraction for current authenticated user
async def get_current_user_id(
    # In full runtime, injects from Agent 3's auth token verification dependency
    # e.g. token: str = Depends(oauth2_scheme) -> extracts auth.uid()
) -> str:
    # Defaulting to demonstration UUID representing authenticated founder Taj
    return "00000000-0000-0000-0000-000000000001"


# Dependency abstraction for Idea Service
def get_idea_service() -> IdeaService:
    # In production, injects Supabase client or DB session pool
    class MockDbClient:
        pass

    return IdeaService(repo=IdeaRepository(db_client=MockDbClient()))


def build_meta() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "v1",
        "module": "idea-vault",
    }


@router.get("", response_model=IdeaListResponse, status_code=status.HTTP_200_OK)
async def list_ideas(
    status_filter: Optional[str] = Query(None, alias="status"),
    venture_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    """List founder ideas with filtering by status and related venture."""
    ideas = await service.list_ideas(user_id, status_filter, venture_id, limit, offset)
    return {
        "data": ideas,
        "pagination": {"limit": limit, "offset": offset, "total": len(ideas)},
        "meta": build_meta(),
    }


@router.post("", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
async def create_idea(
    payload: IdeaCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    """Capture a new startup idea or feature hypothesis."""
    created = await service.create_idea(user_id, payload.model_dump())
    return {"data": created, "meta": build_meta()}


@router.get("/{idea_id}", response_model=IdeaResponse, status_code=status.HTTP_200_OK)
async def get_idea(
    idea_id: str,
    user_id: str = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    """Retrieve specific idea by UUID."""
    idea = await service.get_idea(user_id, idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found or unauthorized.")
    return {"data": idea, "meta": build_meta()}


@router.patch("/{idea_id}", response_model=IdeaResponse, status_code=status.HTTP_200_OK)
async def update_idea(
    idea_id: str,
    payload: IdeaUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    """Update existing idea assumptions, experiments, or metadata."""
    updated = await service.update_idea(user_id, idea_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Idea not found or unauthorized.")
    return {"data": updated, "meta": build_meta()}


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_idea(
    idea_id: str,
    user_id: str = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    """Soft-delete an idea by setting deleted_at timestamp."""
    success = await service.delete_idea(user_id, idea_id)
    if not success:
        raise HTTPException(status_code=404, detail="Idea not found or unauthorized.")
    return None


@router.post(
    "/{idea_id}/convert", response_model=IdeaConversionResponse, status_code=status.HTTP_200_OK
)
async def convert_idea_to_project(
    idea_id: str,
    payload: IdeaToProjectConvertRequest,
    user_id: str = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    """Atomically convert validated idea to actionable project without deleting historical records."""
    try:
        res = await service.convert_to_project(
            user_id, idea_id, payload.model_dump(exclude_unset=True)
        )
        return {"data": res, "meta": build_meta()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{idea_id}/analyze", status_code=status.HTTP_200_OK)
async def analyze_idea(
    idea_id: str,
    user_id: str = Depends(get_current_user_id),
    service: IdeaService = Depends(get_idea_service),
):
    """Trigger Gemini AI strategic feasibility evaluation."""
    try:
        res = await service.analyze_idea_feasibility(user_id, idea_id)
        return {"data": res, "meta": build_meta()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
