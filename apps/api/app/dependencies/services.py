from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import get_db_session
from app.services.founder import (
    DashboardService,
    KPIService,
    ProfileService,
    ProjectService,
    ReviewService,
    TaskService,
    VentureService,
)
from app.services.integrations import AuditService, ExportService, IntegrationManagementService
from app.services.knowledge import (
    AchievementService,
    AIService,
    ContentService,
    DecisionService,
    DocumentService,
    IdeaService,
    MemoryService,
    PortfolioService,
)
from app.services.network import (
    InteractionService,
    MeetingService,
    OrganizationService,
    PersonService,
)


def get_profile_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> ProfileService:
    return ProfileService(db, user.id)


def get_venture_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> VentureService:
    return VentureService(db, user.id)


def get_project_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> ProjectService:
    return ProjectService(db, user.id)


def get_task_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> TaskService:
    return TaskService(db, user.id)


def get_kpi_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> KPIService:
    return KPIService(db, user.id)


def get_review_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> ReviewService:
    return ReviewService(db, user.id)


def get_dashboard_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> DashboardService:
    return DashboardService(db, user.id)


def get_person_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> PersonService:
    return PersonService(db, user.id)


def get_organization_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> OrganizationService:
    return OrganizationService(db, user.id)


def get_interaction_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> InteractionService:
    return InteractionService(db, user.id)


def get_meeting_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> MeetingService:
    return MeetingService(db, user.id)


def get_memory_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> MemoryService:
    return MemoryService(db, user.id)


def get_idea_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> IdeaService:
    return IdeaService(db, user.id)


def get_decision_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> DecisionService:
    return DecisionService(db, user.id)


def get_document_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> DocumentService:
    return DocumentService(db, user.id)


def get_ai_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> AIService:
    return AIService(db, user.id)


def get_achievement_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> AchievementService:
    return AchievementService(db, user.id)


def get_portfolio_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> PortfolioService:
    return PortfolioService(db, user.id)


def get_content_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> ContentService:
    return ContentService(db, user.id)


def get_integration_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> IntegrationManagementService:
    return IntegrationManagementService(db, user.id)


def get_export_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> ExportService:
    return ExportService(db, user.id)


def get_audit_service(
    db: AsyncSession = Depends(get_db_session), user: AuthenticatedUser = Depends(get_current_user)
) -> AuditService:
    return AuditService(db, user.id)
