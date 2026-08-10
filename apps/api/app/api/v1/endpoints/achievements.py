"""
Achievement Portfolio FastAPI Router
Module Owner: Agent 9
Endpoints: /api/v1/achievements
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.achievements import AchievementRepository
from app.schemas.achievement import (
    AchievementCreateRequest,
    AchievementListResponse,
    AchievementResponse,
    AchievementUpdateRequest,
)
from app.services.achievements.achievement_service import AchievementService

router = APIRouter()


async def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


def get_achievement_service() -> AchievementService:
    class MockDbClient:
        pass

    return AchievementService(repo=AchievementRepository(db_client=MockDbClient()))


def build_meta() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "v1",
        "module": "achievement-portfolio",
    }


@router.get("", response_model=AchievementListResponse, status_code=status.HTTP_200_OK)
async def list_achievements(
    venture_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    service: AchievementService = Depends(get_achievement_service),
):
    """List founder achievements sorted chronologically."""
    achievements = await service.list_achievements(user_id, venture_id, limit, offset)
    return {
        "data": achievements,
        "pagination": {"limit": limit, "offset": offset, "total": len(achievements)},
        "meta": build_meta(),
    }


@router.post("", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED)
async def create_achievement(
    payload: AchievementCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: AchievementService = Depends(get_achievement_service),
):
    """Record a verified career achievement with supporting evidence links."""
    created = await service.create_achievement(user_id, payload.model_dump())
    return {"data": created, "meta": build_meta()}


@router.get("/{achievement_id}", response_model=AchievementResponse, status_code=status.HTTP_200_OK)
async def get_achievement(
    achievement_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AchievementService = Depends(get_achievement_service),
):
    """Retrieve specific achievement by UUID."""
    ach = await service.get_achievement(user_id, achievement_id)
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found or unauthorized.")
    return {"data": ach, "meta": build_meta()}


@router.patch(
    "/{achievement_id}", response_model=AchievementResponse, status_code=status.HTTP_200_OK
)
async def update_achievement(
    achievement_id: str,
    payload: AchievementUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: AchievementService = Depends(get_achievement_service),
):
    """Update achievement details or evidence attachments."""
    updated = await service.update_achievement(
        user_id, achievement_id, payload.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Achievement not found or unauthorized.")
    return {"data": updated, "meta": build_meta()}


@router.delete("/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_achievement(
    achievement_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AchievementService = Depends(get_achievement_service),
):
    """Soft-delete an achievement."""
    success = await service.delete_achievement(user_id, achievement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Achievement not found or unauthorized.")
    return None
