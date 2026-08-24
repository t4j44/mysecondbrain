from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile, status

from app.core.pagination import PaginatedResponse, PaginationParams
from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.services import (
    DecisionService,
    DocumentService,
    IdeaService,
    MemoryService,
    get_decision_service,
    get_document_service,
    get_idea_service,
    get_memory_service,
)
from app.schemas.knowledge import (
    DecisionCreate,
    DecisionResponse,
    DecisionUpdate,
    DocumentResponse,
    IdeaConvertResponse,
    IdeaCreate,
    IdeaResponse,
    IdeaUpdate,
    MemoryCreate,
    MemoryResponse,
    MemoryUpdate,
)

router = APIRouter()


# --- MEMORIES ENDPOINTS (Task 18) ---
@router.post(
    "/memories",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Capture personal note, reflection, or meeting synthesis",
)
async def create_memory(
    payload: MemoryCreate,
    service: MemoryService = Depends(get_memory_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_memory(payload.model_dump())


@router.get(
    "/memories",
    response_model=PaginatedResponse[MemoryResponse],
    summary="List captured founder memories and intelligence items",
)
async def list_memories(
    type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: MemoryService = Depends(get_memory_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_memories(pagination, type=type)
    return res


@router.get(
    "/memories/{id}", response_model=MemoryResponse, summary="Get canonical memory record by ID"
)
async def read_memory(
    id: str,
    service: MemoryService = Depends(get_memory_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_memory(id)


@router.patch(
    "/memories/{id}", response_model=MemoryResponse, summary="Update canonical memory record"
)
async def update_memory(
    id: str,
    payload: MemoryUpdate,
    service: MemoryService = Depends(get_memory_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_memory(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/memories/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Archive or delete memory record"
)
async def delete_memory(
    id: str,
    service: MemoryService = Depends(get_memory_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_memory(id)


# --- IDEAS ENDPOINTS (Task 19) ---
@router.post(
    "/ideas",
    response_model=IdeaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register potential venture hypothesis or product idea",
)
async def create_idea(
    payload: IdeaCreate,
    service: IdeaService = Depends(get_idea_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_idea(payload.model_dump())


@router.get(
    "/ideas",
    response_model=PaginatedResponse[IdeaResponse],
    summary="List venture hypotheses and innovation concepts",
)
async def list_ideas(
    status_val: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: IdeaService = Depends(get_idea_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_ideas(pagination, status=status_val)
    return res


@router.get(
    "/ideas/{id}",
    response_model=IdeaResponse,
    summary="Retrieve single venture idea details",
)
async def read_idea(
    id: str,
    service: IdeaService = Depends(get_idea_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_idea(id)


@router.patch(
    "/ideas/{id}",
    response_model=IdeaResponse,
    summary="Update venture hypothesis or status",
)
async def update_idea(
    id: str,
    payload: IdeaUpdate,
    service: IdeaService = Depends(get_idea_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_idea(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/ideas/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive or remove venture idea",
)
async def delete_idea(
    id: str,
    service: IdeaService = Depends(get_idea_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_idea(id)


@router.post(
    "/ideas/{id}/convert",
    response_model=IdeaConvertResponse,
    summary="Transform validated idea into an actionable project",
)
async def convert_idea_to_project(
    id: str,
    service: IdeaService = Depends(get_idea_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    _idea, project_id = await service.convert_to_project(id)
    return IdeaConvertResponse(idea_id=id, project_id=project_id)


# --- DECISIONS ENDPOINTS (Task 20) ---
@router.post(
    "/decisions",
    response_model=DecisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log critical executive decision with alternatives and rationale",
)
async def create_decision(
    payload: DecisionCreate,
    service: DecisionService = Depends(get_decision_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.create_decision(payload.model_dump())


@router.get(
    "/decisions",
    response_model=PaginatedResponse[DecisionResponse],
    summary="List historical founder decision logs",
)
async def list_decisions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DecisionService = Depends(get_decision_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_decisions(pagination)
    return res


@router.get(
    "/decisions/{id}",
    response_model=DecisionResponse,
    summary="Retrieve decision log by ID",
)
async def read_decision(
    id: str,
    service: DecisionService = Depends(get_decision_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.get_decision(id)


@router.patch(
    "/decisions/{id}",
    response_model=DecisionResponse,
    summary="Update decision details and impact",
)
async def update_decision(
    id: str,
    payload: DecisionUpdate,
    service: DecisionService = Depends(get_decision_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    return await service.update_decision(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/decisions/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove decision log entry",
)
async def delete_decision(
    id: str,
    service: DecisionService = Depends(get_decision_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_decision(id)


# --- DOCUMENTS ENDPOINTS (Task 21) ---
@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload proprietary PDF or document for RAG ingestion",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    content = await file.read()
    filename = file.filename or "unnamed_upload.pdf"
    content_type = file.content_type or "application/octet-stream"
    return await service.upload_document(
        filename, content, content_type, background_tasks=background_tasks
    )


@router.get(
    "/documents",
    response_model=PaginatedResponse[DocumentResponse],
    summary="List ingested documents and indexing states",
)
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: DocumentService = Depends(get_document_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    pagination = PaginationParams(limit=limit, offset=offset)
    res = await service.list_documents(pagination)
    return res


@router.delete(
    "/documents/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete uploaded document",
)
async def delete_document(
    id: str,
    service: DocumentService = Depends(get_document_service),
    _user: AuthenticatedUser = Depends(get_current_user),
):
    await service.delete_document(id)
