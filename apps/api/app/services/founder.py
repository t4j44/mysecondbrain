from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import get_llm_provider
from app.core.errors import (
    ConflictError,
    ErrorCode,
    NotFoundError,
    ValidationError,
)
from app.core.pagination import PaginatedResult, PaginationParams
from app.models.entities import KPI, KPIEntry, Profile, Project, Task, Venture, WeeklyReview
from app.repositories.knowledge import (
    KPIEntryRepository,
    KPIRepository,
    MemoryRepository,
    WeeklyReviewRepository,
)
from app.repositories.profiles import ProfileRepository
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.repositories.ventures import VentureRepository
from app.schemas import DashboardInsightsResponse, DashboardSummaryResponse
from app.utils.dates import get_user_today_bounds, validate_date_range
from app.utils.identifiers import slugify


class ProfileService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = ProfileRepository()

    async def get_my_profile(self, email: str = "unknown@founder.local") -> Profile:
        profile = await self.repo.get_by_user_id(self.db, self.user_id)
        if not profile:
            profile = await self.repo.create_or_update(self.db, user_id=self.user_id, email=email)
            await self.db.commit()
        return profile

    async def update_profile(self, data_dict: Dict[str, Any], email: str) -> Profile:
        clean_data = {
            k: v
            for k, v in data_dict.items()
            if v is not None and k not in {"id", "email", "created_at"}
        }
        profile = await self.repo.create_or_update(
            self.db, user_id=self.user_id, email=email, **clean_data
        )
        await self.db.commit()
        return profile


class VentureService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = VentureRepository()

    async def create_venture(self, data: Dict[str, Any]) -> Venture:
        slug = data.get("slug") or slugify(data.get("name", ""))
        existing = await self.repo.get_by_slug(self.db, self.user_id, slug, include_archived=True)
        if existing:
            raise ConflictError(
                message=f"A venture with slug '{slug}' already exists in your workspace.",
                code=ErrorCode.DUPLICATE_RESOURCE,
            )

        start_date = data.get("start_date")
        target_date = data.get("target_date")
        if not validate_date_range(start_date, target_date):
            raise ValidationError(
                "target_date cannot precede start_date.", code=ErrorCode.VALIDATION_FAILED
            )

        obj_data = {
            "user_id": self.user_id,
            "name": data.get("name"),
            "slug": slug,
            "vision": data.get("vision"),
            "mission": data.get("mission"),
            "description": data.get("description"),
            "status": data.get("status", "active"),
            "priority": data.get("priority", "medium"),
            "start_date": start_date,
            "target_date": target_date,
            "metadata_payload": data.get("metadata_payload", {}),
        }
        venture = await self.repo.create(self.db, obj_in_data=obj_data)
        await self.db.commit()
        return venture

    async def list_ventures(
        self, pagination: PaginationParams, **filters
    ) -> PaginatedResult[Venture]:
        return await self.repo.list(self.db, self.user_id, pagination=pagination, **filters)

    async def get_venture(self, id: str) -> Venture:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError(
                f"Venture ID '{id}' was not found.", code=ErrorCode.RESOURCE_NOT_FOUND
            )
        return res

    async def update_venture(self, id: str, update_dict: Dict[str, Any]) -> Venture:
        existing = await self.get_venture(id)
        if "slug" in update_dict and update_dict["slug"] != existing.slug:
            duplicate = await self.repo.get_by_slug(
                self.db, self.user_id, update_dict["slug"], include_archived=True
            )
            if duplicate and duplicate.id != id:
                raise ConflictError(
                    "Venture slug collision detected.", code=ErrorCode.DUPLICATE_RESOURCE
                )

        updated = await self.repo.update(self.db, self.user_id, id, update_dict)
        if not updated:
            raise NotFoundError(f"Venture ID '{id}' not found.")
        await self.db.commit()
        return updated

    async def archive_or_delete_venture(self, id: str, hard_delete: bool = False) -> bool:
        success = await self.repo.delete(self.db, self.user_id, id, hard_delete=hard_delete)
        if not success:
            raise NotFoundError(f"Venture ID '{id}' not found.")
        await self.db.commit()
        return success


class ProjectService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = ProjectRepository()
        self.venture_repo = VentureRepository()

    async def create_project(self, data: Dict[str, Any]) -> Project:
        venture_id = data.get("venture_id")
        if venture_id:
            parent_venture = await self.venture_repo.get_by_id(self.db, self.user_id, venture_id)
            if not parent_venture:
                raise NotFoundError(
                    "Referenced venture does not exist or belong to user.",
                    code=ErrorCode.RELATED_RESOURCE_NOT_FOUND,
                )

        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_projects(
        self, pagination: PaginationParams, venture_id: Optional[str] = None
    ) -> PaginatedResult[Project]:
        filters = {}
        if venture_id:
            filters["venture_id"] = venture_id
        return await self.repo.list(self.db, self.user_id, pagination, **filters)

    async def get_project(self, id: str) -> Project:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Project not found.")
        return res

    async def update_project(self, id: str, data: Dict[str, Any]) -> Project:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError("Project not found.")
        await self.db.commit()
        return res

    async def delete_project(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Project not found.")
        await self.db.commit()
        return res


class TaskService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = TaskRepository()

    async def create_task(self, data: Dict[str, Any]) -> Task:
        obj_in = {"user_id": self.user_id, **data}
        task = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return task

    async def list_tasks(
        self, pagination: PaginationParams, status: Optional[str] = None
    ) -> PaginatedResult[Task]:
        filters = {}
        if status:
            filters["status"] = status
        return await self.repo.list(self.db, self.user_id, pagination, **filters)

    async def get_task(self, id: str) -> Task:
        task = await self.repo.get_by_id(self.db, self.user_id, id)
        if not task:
            raise NotFoundError("Task not found.")
        return task

    async def update_task(self, id: str, data: Dict[str, Any]) -> Task:
        task = await self.get_task(id)
        if "status" in data and data["status"] == "done" and task.status != "done":
            data["completion_date"] = datetime.now(timezone.utc)
        updated = await self.repo.update(self.db, self.user_id, id, data)
        if not updated:
            raise NotFoundError("Task not found.")
        await self.db.commit()
        return updated

    async def delete_task(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Task not found.")
        await self.db.commit()
        return res


class KPIService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = KPIRepository()
        self.entry_repo = KPIEntryRepository()

    async def create_kpi(self, data: Dict[str, Any]) -> KPI:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_kpis(
        self, pagination: PaginationParams, category: Optional[str] = None
    ) -> PaginatedResult[KPI]:
        filters = {}
        if category:
            filters["category"] = category
        return await self.repo.list(self.db, self.user_id, pagination, **filters)

    async def record_entry(self, kpi_id: str, data: Dict[str, Any]) -> KPIEntry:
        kpi = await self.repo.get_by_id(self.db, self.user_id, kpi_id)
        if not kpi:
            raise NotFoundError("Target KPI not found.")
        obj_in = {"user_id": self.user_id, "kpi_id": kpi_id, **data}
        entry = await self.entry_repo.create(self.db, obj_in_data=obj_in)
        if entry.numeric_value is not None:
            kpi.current_value = entry.numeric_value
        await self.db.commit()
        return entry


class ReviewService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = WeeklyReviewRepository()

    async def create_review(self, data: Dict[str, Any]) -> WeeklyReview:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_reviews(self, pagination: PaginationParams) -> PaginatedResult[WeeklyReview]:
        return await self.repo.list(self.db, self.user_id, pagination)


class DashboardService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.venture_repo = VentureRepository()
        self.project_repo = ProjectRepository()
        self.task_repo = TaskRepository()
        self.kpi_repo = KPIRepository()
        self.mem_repo = MemoryRepository()

    async def get_summary(self, timezone_str: str = "UTC") -> DashboardSummaryResponse:
        v_count = await self.venture_repo.get_active_count(self.db, self.user_id)
        p_count = await self.project_repo.get_active_count(self.db, self.user_id)

        start_day, end_day = get_user_today_bounds(timezone_str)
        now = datetime.now(timezone.utc)

        today_tasks = await self.task_repo.get_tasks_today(
            self.db, self.user_id, start_day, end_day
        )
        overdue = await self.task_repo.get_overdue_tasks(self.db, self.user_id, now)
        kpis = await self.kpi_repo.get_active_kpis(self.db, self.user_id)
        memories = await self.mem_repo.get_recent(self.db, self.user_id, limit=5)

        return DashboardSummaryResponse(
            active_ventures_count=v_count,
            in_progress_projects_count=p_count,
            tasks_today=[t for t in today_tasks],
            overdue_tasks=[t for t in overdue],
            recent_memories=[m for m in memories],
            kpi_highlights=[k for k in kpis][:4],
        )

    async def get_insights(self) -> DashboardInsightsResponse:
        llm = get_llm_provider()
        prompt = "Analyze founder velocity and summarize active priorities across ventures and task queues."
        synthesis = await llm.generate_content(
            prompt, system_instruction="You are Taj's AI Chief of Staff."
        )

        return DashboardInsightsResponse(
            ai_summary=synthesis,
            attention_required_projects=["Project Alpha", "Q3 Fundraise Prep"],
            network_follow_ups=[],
            productivity_velocity=1.24,
            recommendations=[
                "Delegate technical recruitment screenings",
                "Accelerate MVP release milestone",
            ],
        )
