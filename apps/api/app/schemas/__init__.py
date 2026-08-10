"""
Explicit Schema Exports for Taj's Second Brain API Schema Package
"""

from app.schemas.crm import (
    OrganizationCreate as CRMOrganizationCreate,
)
from app.schemas.crm import (
    OrganizationResponse as CRMOrganizationResponse,
)
from app.schemas.crm import (
    OrganizationUpdate as CRMOrganizationUpdate,
)
from app.schemas.crm import (
    PersonCreate as CRMPersonCreate,
)
from app.schemas.crm import (
    PersonResponse as CRMPersonResponse,
)
from app.schemas.crm import (
    PersonUpdate as CRMPersonUpdate,
)
from app.schemas.crm import (
    RelationshipCreateRequest,
    RelationshipResponse,
)
from app.schemas.founder import (
    DashboardInsightsResponse,
    DashboardSummaryResponse,
    KPICreate,
    KPIEntryCreate,
    KPIUpdate,
    ProfileResponse,
    ProfileUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    VentureCreate,
    VentureResponse,
    VentureUpdate,
    WeeklyReviewCreate,
    WeeklyReviewResponse,
)
from app.schemas.integrations import (
    AuditLogResponse,
    ExportRequest,
    ExportResponse,
    GoogleCallbackRequest,
    GoogleCallbackResponse,
    IntegrationResponse,
    JobResponse,
    SyncCalendarRequest,
    SyncDriveRequest,
)
from app.schemas.interactions import (
    InteractionCreate,
    InteractionResponse,
    InteractionUpdate,
)
from app.schemas.knowledge import (
    AchievementCreate,
    AchievementResponse,
    AchievementUpdate,
    AIContentGenerateRequest,
    AIContentGenerateResponse,
    AICoverletterRequest,
    AILinkedInPostRequest,
    ContentCreate,
    ContentResponse,
    ContentUpdate,
    ContentVersionResponse,
    DecisionCreate,
    DecisionResponse,
    DecisionUpdate,
    DocumentProcessResponse,
    DocumentResponse,
    IdeaConvertResponse,
    IdeaCreate,
    IdeaResponse,
    IdeaUpdate,
    MemoryCreate,
    MemoryResponse,
    MemoryUpdate,
    PortfolioCaseStudyCreate,
    PortfolioCaseStudyResponse,
    PortfolioCaseStudyUpdate,
    SearchRequest,
    SearchResultItem,
    SearchResultResponse,
)
from app.schemas.kpi import (
    KPICategory,
    KPIDefinitionCreateRequest,
    KPIDefinitionResource,
    KPIDefinitionUpdateRequest,
    KPIDirection,
    KPIEntryCreateRequest,
    KPIEntryListResponse,
    KPIEntryResource,
    KPIEntryResponse,
    KPIEntryUpdateRequest,
    KPIEvidenceRef,
    KPIListResponse,
    KPIPeriod,
    KPIResponse,
    KPITrend,
)
from app.schemas.mcp import (
    MCPCredentialCreateRequest,
    MCPCredentialCreateResponse,
    MCPCredentialListResponse,
    MCPCredentialMeta,
    MCPCredentialSecretResponse,
)
from app.schemas.meetings import (
    MeetingCreate,
    MeetingResponse,
    MeetingUpdate,
)
from app.schemas.memories import (
    MemoryCreate as DirectMemoryCreate,
)
from app.schemas.memories import (
    MemoryResponse as DirectMemoryResponse,
)
from app.schemas.memories import (
    MemoryUpdate as DirectMemoryUpdate,
)
from app.schemas.network import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    PersonCreate,
    PersonResponse,
    PersonUpdate,
)
from app.schemas.portfolio import (
    CaseStudyCitation,
    CaseStudyListResponse,
    CaseStudyResource,
    CaseStudyResponse,
    CaseStudyUpdateRequest,
    EvidenceCoverageState,
    GenerateCaseStudyRequest,
    ManualCaseStudyCreateRequest,
)

__all__ = [
    # Founder & Profiles
    "ProfileUpdate",
    "ProfileResponse",
    "DashboardSummaryResponse",
    "DashboardInsightsResponse",
    "KPICreate",
    "KPIUpdate",
    "KPIEntryCreate",
    "WeeklyReviewCreate",
    # CRM & Network
    "OrganizationCreate",
    "OrganizationResponse",
    "OrganizationUpdate",
    "PersonCreate",
    "PersonResponse",
    "PersonUpdate",
    "RelationshipCreateRequest",
    "RelationshipResponse",
    "CRMOrganizationCreate",
    "CRMOrganizationResponse",
    "CRMOrganizationUpdate",
    "CRMPersonCreate",
    "CRMPersonResponse",
    "CRMPersonUpdate",
    # Integrations
    "AuditLogResponse",
    "ExportRequest",
    "ExportResponse",
    "GoogleCallbackRequest",
    "GoogleCallbackResponse",
    "IntegrationResponse",
    "JobResponse",
    "SyncCalendarRequest",
    "SyncDriveRequest",
    # Interactions
    "InteractionCreate",
    "InteractionResponse",
    "InteractionUpdate",
    # Knowledge & AI
    "AchievementCreate",
    "AchievementResponse",
    "AchievementUpdate",
    "AIContentGenerateRequest",
    "AIContentGenerateResponse",
    "AICoverletterRequest",
    "AILinkedInPostRequest",
    "ContentCreate",
    "ContentResponse",
    "ContentUpdate",
    "ContentVersionResponse",
    "DocumentProcessResponse",
    "DocumentResponse",
    "IdeaConvertResponse",
    "PortfolioCaseStudyCreate",
    "PortfolioCaseStudyResponse",
    "PortfolioCaseStudyUpdate",
    "SearchRequest",
    "SearchResultItem",
    "SearchResultResponse",
    # KPI
    "KPICategory",
    "KPIDefinitionCreateRequest",
    "KPIDefinitionResource",
    "KPIDefinitionUpdateRequest",
    "KPIDirection",
    "KPIEntryCreateRequest",
    "KPIEntryListResponse",
    "KPIEntryResource",
    "KPIEntryResponse",
    "KPIEntryUpdateRequest",
    "KPIEvidenceRef",
    "KPIListResponse",
    "KPIPeriod",
    "KPIResponse",
    "KPITrend",
    # MCP
    "MCPCredentialCreateRequest",
    "MCPCredentialCreateResponse",
    "MCPCredentialListResponse",
    "MCPCredentialMeta",
    "MCPCredentialSecretResponse",
    # Meetings
    "MeetingCreate",
    "MeetingResponse",
    "MeetingUpdate",
    # Memories
    "MemoryCreate",
    "MemoryResponse",
    "MemoryUpdate",
    "DirectMemoryCreate",
    "DirectMemoryResponse",
    "DirectMemoryUpdate",
    # Portfolio
    "CaseStudyCitation",
    "CaseStudyListResponse",
    "CaseStudyResource",
    "CaseStudyResponse",
    "CaseStudyUpdateRequest",
    "EvidenceCoverageState",
    "GenerateCaseStudyRequest",
    "ManualCaseStudyCreateRequest",
    # Core Entities
    "DecisionCreate",
    "DecisionResponse",
    "DecisionUpdate",
    "IdeaCreate",
    "IdeaResponse",
    "IdeaUpdate",
    "ProjectCreate",
    "ProjectResponse",
    "ProjectUpdate",
    "TaskCreate",
    "TaskResponse",
    "TaskUpdate",
    "VentureCreate",
    "VentureResponse",
    "VentureUpdate",
    "WeeklyReviewResponse",
]
