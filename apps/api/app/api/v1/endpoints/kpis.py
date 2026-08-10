"""
Life KPI System FastAPI Router
Module Owner: Agent 9
Endpoints: /api/v1/kpis
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.kpis import KPIRepository
from app.schemas.kpi import (
    KPIDefinitionCreateRequest,
    KPIDefinitionUpdateRequest,
    KPIEntryCreateRequest,
    KPIEntryListResponse,
    KPIEntryResponse,
    KPIListResponse,
    KPIResponse,
)
from app.services.kpis.kpi_service import KPIService

router = APIRouter()


async def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


def get_kpi_service() -> KPIService:
    class MockDbClient:
        pass

    return KPIService(repo=KPIRepository(db_client=MockDbClient()))


def build_meta() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "v1",
        "module": "life-kpis",
    }


@router.get("", response_model=KPIListResponse, status_code=status.HTTP_200_OK)
async def list_kpi_definitions(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    service: KPIService = Depends(get_kpi_service),
):
    """List tracked KPIs enhanced with real-time non-vanity progress & historical trend analysis."""
    kpis = await service.list_kpis_with_analytics(user_id, category, limit, offset)
    return {
        "data": kpis,
        "pagination": {"limit": limit, "offset": offset, "total": len(kpis)},
        "meta": build_meta(),
    }


@router.post("", response_model=KPIResponse, status_code=status.HTTP_201_CREATED)
async def create_kpi_definition(
    payload: KPIDefinitionCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: KPIService = Depends(get_kpi_service),
):
    """Create a new KPI definition."""
    created = await service.repo.create_kpi(user_id, payload.model_dump())
    enhanced = await service.get_kpi_with_analytics(user_id, created["id"]) or created
    return {"data": enhanced, "meta": build_meta()}


@router.get("/{kpi_id}", response_model=KPIResponse, status_code=status.HTTP_200_OK)
async def get_kpi_definition(
    kpi_id: str,
    user_id: str = Depends(get_current_user_id),
    service: KPIService = Depends(get_kpi_service),
):
    """Retrieve specific KPI with analytics and recent entry records."""
    kpi = await service.get_kpi_with_analytics(user_id, kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found or unauthorized.")
    return {"data": kpi, "meta": build_meta()}


@router.patch("/{kpi_id}", response_model=KPIResponse, status_code=status.HTTP_200_OK)
async def update_kpi_definition(
    kpi_id: str,
    payload: KPIDefinitionUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: KPIService = Depends(get_kpi_service),
):
    """Update KPI target or category without modifying historical check-ins."""
    updated = await service.repo.update_kpi(user_id, kpi_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="KPI not found or unauthorized.")
    enhanced = await service.get_kpi_with_analytics(user_id, kpi_id) or updated
    return {"data": enhanced, "meta": build_meta()}


@router.delete("/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi_definition(
    kpi_id: str,
    user_id: str = Depends(get_current_user_id),
    service: KPIService = Depends(get_kpi_service),
):
    """Soft-delete a KPI definition."""
    success = await service.repo.delete_kpi(user_id, kpi_id)
    if not success:
        raise HTTPException(status_code=404, detail="KPI not found or unauthorized.")
    return None


@router.post(
    "/{kpi_id}/entries", response_model=KPIEntryResponse, status_code=status.HTTP_201_CREATED
)
async def create_kpi_entry(
    kpi_id: str,
    payload: KPIEntryCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: KPIService = Depends(get_kpi_service),
):
    """Record an historical KPI measurement check-in."""
    try:
        entry = await service.record_entry(user_id, kpi_id, payload.model_dump())
        return {"data": entry, "meta": build_meta()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/{kpi_id}/entries", response_model=KPIEntryListResponse, status_code=status.HTTP_200_OK
)
async def list_kpi_entries(
    kpi_id: str,
    limit: int = Query(100, ge=1, le=500),
    user_id: str = Depends(get_current_user_id),
    service: KPIService = Depends(get_kpi_service),
):
    """List chronological KPI measurement check-ins."""
    kpi = await service.repo.get_kpi(user_id, kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found or unauthorized.")
    entries = await service.repo.list_entries(user_id, kpi_id, limit)
    return {"data": entries, "meta": build_meta()}
