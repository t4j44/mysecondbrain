"""
Portfolio Case Studies FastAPI Router
Module Owner: Agent 9
Endpoints: /api/v1/portfolio
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.repositories.achievements import AchievementRepository
from app.repositories.portfolio import PortfolioRepository
from app.schemas.portfolio import (
    CaseStudyListResponse,
    CaseStudyResponse,
    CaseStudyUpdateRequest,
    GenerateCaseStudyRequest,
    ManualCaseStudyCreateRequest,
)
from app.services.portfolio.portfolio_service import PortfolioService

router = APIRouter()


async def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


def get_portfolio_service() -> PortfolioService:
    class MockDbClient:
        pass

    client = MockDbClient()
    return PortfolioService(
        repo=PortfolioRepository(db_client=client),
        achievement_repo=AchievementRepository(db_client=client),
    )


def build_meta() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_version": "v1",
        "module": "portfolio-case-studies",
    }


@router.get("/case-studies", response_model=CaseStudyListResponse, status_code=status.HTTP_200_OK)
async def list_case_studies(
    target_role: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """List generated and authored portfolio case studies."""
    case_studies = await service.list_case_studies(user_id, target_role, limit, offset)
    return {
        "data": case_studies,
        "pagination": {"limit": limit, "offset": offset, "total": len(case_studies)},
        "meta": build_meta(),
    }


@router.post("/generate", response_model=CaseStudyResponse, status_code=status.HTTP_201_CREATED)
async def generate_case_study(
    payload: GenerateCaseStudyRequest,
    user_id: str = Depends(get_current_user_id),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """Synthesize executive case study from verified achievements without fabricated metrics."""
    try:
        created = await service.generate_grounded_case_study(user_id, payload.model_dump())
        return {"data": created, "meta": build_meta()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/case-studies", response_model=CaseStudyResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_case_study(
    payload: ManualCaseStudyCreateRequest,
    user_id: str = Depends(get_current_user_id),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """Manually author a portfolio case study."""
    created = await service.create_manual_case_study(user_id, payload.model_dump())
    return {"data": created, "meta": build_meta()}


@router.get("/case-studies/{id}", response_model=CaseStudyResponse, status_code=status.HTTP_200_OK)
async def get_case_study(
    id: str,
    user_id: str = Depends(get_current_user_id),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """Retrieve specific portfolio case study by UUID."""
    cs = await service.get_case_study(user_id, id)
    if not cs:
        raise HTTPException(status_code=404, detail="Case study not found or unauthorized.")
    return {"data": cs, "meta": build_meta()}


@router.patch(
    "/case-studies/{id}", response_model=CaseStudyResponse, status_code=status.HTTP_200_OK
)
async def update_case_study(
    id: str,
    payload: CaseStudyUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """Update case study sections or publication status."""
    updated = await service.update_case_study(user_id, id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Case study not found or unauthorized.")
    return {"data": updated, "meta": build_meta()}


@router.delete("/case-studies/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_study(
    id: str,
    user_id: str = Depends(get_current_user_id),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """Soft-delete a case study."""
    success = await service.delete_case_study(user_id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Case study not found or unauthorized.")
    return None
