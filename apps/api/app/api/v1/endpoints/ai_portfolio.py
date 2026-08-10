from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.pagination import PaginationParams
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.services import (
    AchievementService,
    AIService,
    ContentService,
    PortfolioService,
    get_achievement_service,
    get_ai_service,
    get_content_service,
    get_portfolio_service,
)
from app.schemas import (
    AchievementCreate,
    AchievementResponse,
    AIContentGenerateRequest,
    AIContentGenerateResponse,
    AICoverletterRequest,
    AILinkedInPostRequest,
    ContentCreate,
    ContentResponse,
    ContentUpdate,
    ContentVersionResponse,
    PortfolioCaseStudyCreate,
    PortfolioCaseStudyResponse,
    SearchRequest,
    SearchResultResponse,
)

router = APIRouter()


# --- SEARCH & AI ENDPOINTS (Tasks 22 & 23) ---
@router.get(
    "/search",
    response_model=SearchResultResponse,
    summary="Execute semantic hybrid search across all founder knowledge",
)
@router.post(
    "/ai/search",
    response_model=SearchResultResponse,
    summary="Execute AI semantic query (api_contracts.md standard)",
)
async def execute_knowledge_search(
    query: Optional[str] = Query(""),
    payload: Optional[SearchRequest] = None,
    service: AIService = Depends(get_ai_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    search_term = (payload.query if payload else query) or "founder priorities"
    res = await service.execute_search(search_term, limit=10)
    return SearchResultResponse(**res)


@router.post(
    "/ai/content-generate",
    response_model=AIContentGenerateResponse,
    summary="Generate grounded AI content with source citations",
)
async def ai_generate_content(
    payload: AIContentGenerateRequest,
    service: AIService = Depends(get_ai_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    res = await service.generate_content_with_rag(payload.prompt, payload.context_record_ids)
    return AIContentGenerateResponse(**res)


@router.post(
    "/ai/cover-letter",
    response_model=dict,
    summary="Generate executive cover letter derived from canonical impact metrics",
)
async def ai_cover_letter(
    payload: AICoverletterRequest,
    service: AIService = Depends(get_ai_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    text = await service.generate_cover_letter(
        payload.achievement_id,
        payload.target_role,
        payload.company_name,
        payload.job_description or "",
    )
    return {"cover_letter_text": text, "provider": "google_gemini"}


@router.post(
    "/ai/linkedin-post",
    response_model=dict,
    summary="Synthesize high-performing technical LinkedIn post from achievements",
)
async def ai_linkedin_post(
    payload: AILinkedInPostRequest,
    service: AIService = Depends(get_ai_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    text = await service.generate_linkedin_post(
        payload.achievement_id, payload.tone, payload.include_hashtags
    )
    return {"post_text": text, "provider": "google_gemini"}


# --- ACHIEVEMENTS & PORTFOLIO ENDPOINTS (Tasks 25 & 26) ---
@router.post(
    "/achievements",
    response_model=AchievementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record milestone or historical career achievement",
)
async def create_achievement(
    payload: AchievementCreate,
    service: AchievementService = Depends(get_achievement_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_achievement(payload.model_dump())


@router.get(
    "/achievements", response_model=dict, summary="List verified career impact achievements"
)
async def list_achievements(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: AchievementService = Depends(get_achievement_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_achievements(pagination)
    return res.model_dump()


@router.post(
    "/portfolio/case-studies",
    response_model=PortfolioCaseStudyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish executive portfolio case study",
)
async def create_case_study(
    payload: PortfolioCaseStudyCreate,
    service: PortfolioService = Depends(get_portfolio_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_case_study(payload.model_dump())


@router.get(
    "/portfolio/case-studies", response_model=dict, summary="List executive portfolio case studies"
)
async def list_case_studies(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: PortfolioService = Depends(get_portfolio_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_case_studies(pagination)
    return res.model_dump()


# --- CONTENT ENDPOINTS (Task 27) ---
@router.post(
    "/content",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create strategic article, memo, or newsletter draft",
)
async def create_content(
    payload: ContentCreate,
    service: ContentService = Depends(get_content_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_content(payload.model_dump())


@router.get("/content", response_model=dict, summary="List authored content items across stages")
async def list_content(
    content_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ContentService = Depends(get_content_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_content(pagination, content_type=content_type)
    return res.model_dump()


@router.patch(
    "/content/{id}",
    response_model=ContentResponse,
    summary="Update content body and generate version record",
)
async def update_content(
    id: str,
    payload: ContentUpdate,
    service: ContentService = Depends(get_content_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_content(id, payload.model_dump(exclude_unset=True))


@router.get(
    "/content/{id}/versions",
    response_model=list[ContentVersionResponse],
    summary="Retrieve complete chronological revision history for content piece",
)
async def list_content_versions(
    id: str,
    service: ContentService = Depends(get_content_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.list_versions(id)
