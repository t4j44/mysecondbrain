from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.pagination import PaginationParams
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.services import (
    CommitmentService,
    InteractionService,
    MeetingService,
    NetworkIntelligenceService,
    OrganizationService,
    PersonOrganizationRoleService,
    PersonService,
    get_commitment_service,
    get_interaction_service,
    get_meeting_service,
    get_network_intelligence_service,
    get_organization_service,
    get_person_organization_role_service,
    get_person_service,
)
from app.schemas import (
    CommitmentCreate,
    CommitmentResponse,
    CommitmentUpdate,
    InteractionCreate,
    InteractionResponse,
    InteractionUpdate,
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
    NetworkOverviewResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationSummaryResponse,
    OrganizationUpdate,
    PersonCreate,
    PersonOrganizationRoleCreate,
    PersonOrganizationRoleResponse,
    PersonOrganizationRoleUpdate,
    PersonResponse,
    PersonUpdate,
    StaleContactResponse,
    VentureNetworkEntry,
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


# --- PERSON ↔ ORGANIZATION ROLE ENDPOINTS (G5.5) ---
@router.post(
    "/people/{person_id}/organizations",
    response_model=PersonOrganizationRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Affiliate a contact with an organization in a specific role",
)
async def create_person_organization_role(
    person_id: str,
    payload: PersonOrganizationRoleCreate,
    service: PersonOrganizationRoleService = Depends(get_person_organization_role_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_role({"person_id": person_id, **payload.model_dump()})


@router.get(
    "/people/{person_id}/organizations",
    response_model=List[PersonOrganizationRoleResponse],
    summary="List every organization a contact belongs to, including ended affiliations",
)
async def list_person_organization_roles(
    person_id: str,
    include_ended: bool = Query(True),
    service: PersonOrganizationRoleService = Depends(get_person_organization_role_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.list_roles_for_person(person_id, include_ended=include_ended)


@router.patch(
    "/network/roles/{id}",
    response_model=PersonOrganizationRoleResponse,
    summary="Update or end an organization affiliation",
)
async def update_person_organization_role(
    id: str,
    payload: PersonOrganizationRoleUpdate,
    service: PersonOrganizationRoleService = Depends(get_person_organization_role_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_role(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/network/roles/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an organization affiliation record",
)
async def delete_person_organization_role(
    id: str,
    service: PersonOrganizationRoleService = Depends(get_person_organization_role_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_role(id)


# --- COMMITMENT ENDPOINTS (G5.5) ---
@router.post(
    "/commitments",
    response_model=CommitmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a commitment owed to me or by me",
)
async def create_commitment(
    payload: CommitmentCreate,
    service: CommitmentService = Depends(get_commitment_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_commitment(payload.model_dump())


@router.get(
    "/commitments",
    response_model=List[CommitmentResponse],
    summary="Query the commitment ledger by direction, status, counterparty or overdue state",
)
async def list_commitments(
    person_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    venture_id: Optional[str] = None,
    direction: Optional[str] = Query(None, pattern="^(owed_to_me|owed_by_me|unspecified)$"),
    commitment_status: Optional[str] = Query(None, pattern="^(open|completed|cancelled)$"),
    overdue_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    service: CommitmentService = Depends(get_commitment_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.list_commitments(
        person_id=person_id,
        organization_id=organization_id,
        venture_id=venture_id,
        direction=direction,
        status=commitment_status,
        overdue_only=overdue_only,
        limit=limit,
    )


@router.get(
    "/commitments/{id}",
    response_model=CommitmentResponse,
    summary="Retrieve a commitment by ID",
)
async def read_commitment(
    id: str,
    service: CommitmentService = Depends(get_commitment_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_commitment(id)


@router.patch(
    "/commitments/{id}",
    response_model=CommitmentResponse,
    summary="Update a commitment",
)
async def update_commitment(
    id: str,
    payload: CommitmentUpdate,
    service: CommitmentService = Depends(get_commitment_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_commitment(id, payload.model_dump(exclude_unset=True))


@router.post(
    "/commitments/{id}/complete",
    response_model=CommitmentResponse,
    summary="Mark a commitment as kept",
)
async def complete_commitment(
    id: str,
    service: CommitmentService = Depends(get_commitment_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.complete_commitment(id)


@router.delete(
    "/commitments/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a commitment record",
)
async def delete_commitment(
    id: str,
    service: CommitmentService = Depends(get_commitment_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_commitment(id)


# --- NETWORK INTELLIGENCE ENDPOINTS (G5.5) ---
@router.get(
    "/network/overview",
    response_model=NetworkOverviewResponse,
    summary="Count the organizations in the network, optionally filtered by industry",
)
async def network_overview(
    industry: Optional[str] = None,
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.network_overview(industry)


@router.get(
    "/organizations/{id}/summary",
    response_model=OrganizationSummaryResponse,
    summary="Structured relationship metrics for one organization",
)
async def organization_summary(
    id: str,
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.organization_summary(id)


@router.get(
    "/organizations/{id}/people",
    response_model=List[Dict[str, Any]],
    summary="Who I know at an organization, their role, and when we last spoke",
)
async def organization_people(
    id: str,
    include_ended: bool = Query(True),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.organization_people(id, include_ended=include_ended)


@router.get(
    "/network/people/{person_id}/relationship",
    response_model=Dict[str, Any],
    summary="Affiliations, last contact and both commitment ledgers for one contact",
)
async def person_relationship(
    person_id: str,
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.person_relationship(person_id)


@router.get(
    "/network/stale-contacts",
    response_model=List[StaleContactResponse],
    summary="Contacts not spoken to within N days, optionally founders only",
)
async def stale_contacts(
    days: int = Query(30, ge=1, le=3650),
    role_contains: Optional[str] = None,
    founders_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.stale_contacts(
        days=days, role_contains=role_contains, founders_only=founders_only, limit=limit
    )


@router.get(
    "/network/ventures/{venture_id}/people",
    response_model=List[VentureNetworkEntry],
    summary="Contacts with recorded interactions or commitments against a venture",
)
async def venture_network(
    venture_id: str,
    limit: int = Query(100, ge=1, le=500),
    service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.venture_network(venture_id, limit=limit)
