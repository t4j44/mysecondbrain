from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.pagination import PaginationParams
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.services import (
    InteractionService,
    MeetingService,
    OrganizationService,
    PersonService,
    get_interaction_service,
    get_meeting_service,
    get_organization_service,
    get_person_service,
)
from app.schemas import (
    InteractionCreate,
    InteractionResponse,
    InteractionUpdate,
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    PersonCreate,
    PersonResponse,
    PersonUpdate,
)

router = APIRouter()


# --- PEOPLE ENDPOINTS (Task 15) ---
@router.post(
    "/people",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a contact to founder network CRM",
)
async def create_person(
    payload: PersonCreate,
    service: PersonService = Depends(get_person_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_person(payload.model_dump())


@router.get(
    "/people", response_model=dict, summary="List contacts in founder network with pagination"
)
async def list_people(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: PersonService = Depends(get_person_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_people(pagination)
    return res.model_dump()


@router.get("/people/{id}", response_model=PersonResponse, summary="Retrieve contact details by ID")
async def read_person(
    id: str,
    service: PersonService = Depends(get_person_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_person(id)


@router.patch(
    "/people/{id}",
    response_model=PersonResponse,
    summary="Update contact background and relationship notes",
)
async def update_person(
    id: str,
    payload: PersonUpdate,
    service: PersonService = Depends(get_person_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_person(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/people/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove contact from CRM network",
)
async def delete_person(
    id: str,
    service: PersonService = Depends(get_person_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_person(id)


# --- ORGANIZATIONS ENDPOINTS (Task 15) ---
@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create company or institutional record",
)
async def create_organization(
    payload: OrganizationCreate,
    service: OrganizationService = Depends(get_organization_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_organization(payload.model_dump())


@router.get(
    "/organizations",
    response_model=dict,
    summary="List target companies and portfolio organizations",
)
async def list_organizations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: OrganizationService = Depends(get_organization_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_organizations(pagination)
    return res.model_dump()


@router.get(
    "/organizations/{id}",
    response_model=OrganizationResponse,
    summary="Retrieve organization details by ID",
)
async def read_organization(
    id: str,
    service: OrganizationService = Depends(get_organization_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_organization(id)


@router.patch(
    "/organizations/{id}",
    response_model=OrganizationResponse,
    summary="Update organization details",
)
async def update_organization(
    id: str,
    payload: OrganizationUpdate,
    service: OrganizationService = Depends(get_organization_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_organization(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/organizations/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive or delete organization record",
)
async def delete_organization(
    id: str,
    service: OrganizationService = Depends(get_organization_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_organization(id)


# --- INTERACTIONS ENDPOINTS (Task 16) ---
@router.post(
    "/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log interaction or networking touchpoint",
)
async def create_interaction(
    payload: InteractionCreate,
    service: InteractionService = Depends(get_interaction_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_interaction(payload.model_dump())


@router.get(
    "/interactions", response_model=dict, summary="List chronological relationship interaction log"
)
async def list_interactions(
    person_id: Optional[str] = None,
    venture_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: InteractionService = Depends(get_interaction_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_interactions(pagination, person_id=person_id, venture_id=venture_id)
    return res.model_dump()


@router.get(
    "/interactions/{id}",
    response_model=InteractionResponse,
    summary="Retrieve interaction details by ID",
)
async def read_interaction(
    id: str,
    service: InteractionService = Depends(get_interaction_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_interaction(id)


@router.patch(
    "/interactions/{id}",
    response_model=InteractionResponse,
    summary="Update interaction details",
)
async def update_interaction(
    id: str,
    payload: InteractionUpdate,
    service: InteractionService = Depends(get_interaction_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_interaction(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/interactions/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove interaction log entry",
)
async def delete_interaction(
    id: str,
    service: InteractionService = Depends(get_interaction_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_interaction(id)


# --- MEETINGS ENDPOINTS (Task 17) ---
@router.post(
    "/meetings",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record scheduled meeting minutes and action items",
)
async def create_meeting(
    payload: MeetingCreate,
    service: MeetingService = Depends(get_meeting_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_meeting(payload.model_dump())


@router.get("/meetings", response_model=dict, summary="Retrieve calendar meetings and discussions")
async def list_meetings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: MeetingService = Depends(get_meeting_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_meetings(pagination)
    return res.model_dump()


@router.get(
    "/meetings/{id}",
    response_model=MeetingResponse,
    summary="Retrieve meeting record by ID",
)
async def read_meeting(
    id: str,
    service: MeetingService = Depends(get_meeting_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_meeting(id)


@router.patch(
    "/meetings/{id}",
    response_model=MeetingResponse,
    summary="Update meeting details and minutes",
)
async def update_meeting(
    id: str,
    payload: MeetingUpdate,
    service: MeetingService = Depends(get_meeting_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_meeting(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/meetings/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove meeting record",
)
async def delete_meeting(
    id: str,
    service: MeetingService = Depends(get_meeting_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_meeting(id)
