from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.background import BackgroundTasks

from app.ai.prompts import get_system_prompt
from app.ai.provider import get_llm_provider
from app.ai.retrieval import format_rag_context, perform_keyword_search
from app.core.errors import ConflictError, ErrorCode, NotFoundError
from app.core.pagination import PaginatedResult, PaginationParams
from app.integrations.storage_client import StorageService
from app.models.entities import (
    Achievement,
    ContentItem,
    ContentVersion,
    Decision,
    Document,
    Idea,
    Memory,
    PortfolioCaseStudy,
)
from app.repositories.integrations import JobRepository
from app.repositories.knowledge import (
    AchievementRepository,
    ContentRepository,
    ContentVersionRepository,
    DecisionRepository,
    DocumentRepository,
    IdeaRepository,
    MemoryRepository,
    PortfolioCaseStudyRepository,
)
from app.repositories.projects import ProjectRepository


class MemoryService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = MemoryRepository()

    async def create_memory(self, data: Dict[str, Any]) -> Memory:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_memories(
        self, pagination: PaginationParams, type: Optional[str] = None
    ) -> PaginatedResult[Memory]:
        filters = {}
        if type:
            filters["type"] = type
        return await self.repo.list(self.db, self.user_id, pagination, **filters)

    async def get_memory(self, id: str) -> Memory:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Memory record not found.")
        return res

    async def update_memory(self, id: str, data: Dict[str, Any]) -> Memory:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError('Memory not found.')
        await self.db.commit()
        return res

    async def delete_memory(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Memory not found.')
        await self.db.commit()
        return res


class IdeaService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = IdeaRepository()
        self.proj_repo = ProjectRepository()

    async def create_idea(self, data: Dict[str, Any]) -> Idea:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_ideas(
        self, pagination: PaginationParams, status: Optional[str] = None
    ) -> PaginatedResult[Idea]:
        filters = {}
        if status:
            filters["status"] = status
        return await self.repo.list(self.db, self.user_id, pagination, **filters)

    async def get_idea(self, id: str) -> Idea:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError("Idea not found.")
        return res

    async def convert_to_project(self, idea_id: str) -> Tuple[Idea, str]:
        idea = await self.get_idea(idea_id)
        if idea.status == "converted":
            raise ConflictError(
                "Idea has already been converted into a project.", code=ErrorCode.CONFLICT
            )

        proj = await self.proj_repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "venture_id": idea.venture_id,
                "name": f"Project: {idea.title}",
                "description": f"Problem: {idea.problem}\nSolution: {idea.solution}",
                "status": "planned",
                "priority": "high",
            },
        )
        idea.status = "converted"
        idea.converted_project_id = str(proj.id)
        idea.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return idea, str(proj.id)

    async def update_idea(self, id: str, data: Dict[str, Any]) -> Idea:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError('Idea not found.')
        await self.db.commit()
        return res

    async def delete_idea(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Idea not found.')
        await self.db.commit()
        return res


class DecisionService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = DecisionRepository()

    async def create_decision(self, data: Dict[str, Any]) -> Decision:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_decisions(self, pagination: PaginationParams) -> PaginatedResult[Decision]:
        return await self.repo.list(self.db, self.user_id, pagination)

    async def get_decision(self, id: str) -> Decision:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Decision not found.')
        return res

    async def update_decision(self, id: str, data: Dict[str, Any]) -> Decision:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError('Decision not found.')
        await self.db.commit()
        return res

    async def delete_decision(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Decision not found.')
        await self.db.commit()
        return res


class DocumentService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = DocumentRepository()
        self.storage = StorageService()

    async def upload_document(
        self,
        raw_name: str,
        content: bytes,
        mime_type: str,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Document:
        sanitized, ext, size, checksum, storage_path = await self.storage.save_upload(
            self.user_id, raw_name, content, mime_type
        )

        existing = await self.repo.get_by_checksum(self.db, self.user_id, checksum)
        if existing:
            return existing

        doc = await self.repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "filename": raw_name,
                "sanitized_filename": sanitized,
                "mime_type": mime_type,
                "extension": ext,
                "size_bytes": size,
                "checksum": checksum,
                "storage_bucket": self.storage.bucket_name,
                "storage_path": storage_path,
                "processing_status": "pending",
            },
        )
        await self.db.flush()

        job_repo = JobRepository()
        job = await job_repo.create(
            self.db,
            obj_in_data={
                "user_id": self.user_id,
                "job_type": "document_processing",
                "status": "pending",
                "result_payload": {"document_id": doc.id},
            },
        )
        await self.db.commit()

        if background_tasks:
            from app.jobs.runner import process_job_async

            background_tasks.add_task(process_job_async, job.id)

        return doc

    async def list_documents(self, pagination: PaginationParams) -> PaginatedResult[Document]:
        return await self.repo.list(self.db, self.user_id, pagination)

    async def get_document(self, id: str) -> Document:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Document not found.')
        return res

    async def delete_document(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Document not found.')
        await self.db.commit()
        return res


class AIService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.llm = get_llm_provider("gemini")

    async def execute_search(self, query: str, limit: int = 10):
        results = await perform_keyword_search(self.db, self.user_id, query, limit)
        return {"query": query, "results": results, "total_matches": len(results)}

    async def generate_content_with_rag(
        self, prompt: str, record_ids: Optional[List[str]] = None
    ) -> dict:
        if record_ids is None:
            record_ids = []
        rag_items = await perform_keyword_search(self.db, self.user_id, prompt, limit=5)
        context = format_rag_context(rag_items)
        full_prompt = f"{context}\n\nFounder Instruction:\n{prompt}"
        synthesis = await self.llm.generate_content(
            full_prompt, system_instruction=get_system_prompt("default")
        )

        return {
            "generated_text": synthesis,
            "provider_used": "google_gemini",
            "model_used": getattr(self.llm, "model", "gemini-2.5-flash"),
            "source_citations": [i.id for i in rag_items],
        }

    async def generate_cover_letter(
        self, achievement_id: str, target_role: str, company: str, job_desc: str = ""
    ) -> str:
        ach_repo = AchievementRepository()
        ach = await ach_repo.get_by_id(self.db, self.user_id, achievement_id)
        if not ach:
            raise NotFoundError("Achievement record not found for cover letter synthesis.")

        prompt = f"Target Role: {target_role} at {company}.\nJob Desc: {job_desc}\n\nHistorical Proof Point:\nTitle: {ach.title}\nImpact: {ach.impact}"
        return await self.llm.generate_content(
            prompt, system_instruction=get_system_prompt("cover_letter")
        )

    async def generate_linkedin_post(
        self, achievement_id: str, tone: str = "engaging", hashtags: bool = True
    ) -> str:
        ach_repo = AchievementRepository()
        ach = await ach_repo.get_by_id(self.db, self.user_id, achievement_id)
        if not ach:
            raise NotFoundError("Achievement record not found.")
        prompt = f"Milestone: {ach.title}\nRole & Responsibilities: {ach.responsibilities}\nImpact: {ach.impact}\nTone: {tone}\nInclude Hashtags: {hashtags}"
        return await self.llm.generate_content(
            prompt, system_instruction=get_system_prompt("linkedin_post")
        )


class AchievementService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = AchievementRepository()

    async def create_achievement(self, data: Dict[str, Any]) -> Achievement:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_achievements(
        self, pagination: PaginationParams
    ) -> PaginatedResult[Achievement]:
        return await self.repo.list(self.db, self.user_id, pagination)

    async def get_achievement(self, id: str) -> Achievement:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Achievement not found.')
        return res

    async def update_achievement(self, id: str, data: Dict[str, Any]) -> Achievement:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError('Achievement not found.')
        await self.db.commit()
        return res

    async def delete_achievement(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Achievement not found.')
        await self.db.commit()
        return res


class PortfolioService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = PortfolioCaseStudyRepository()

    async def create_case_study(self, data: Dict[str, Any]) -> PortfolioCaseStudy:
        obj_in = {"user_id": self.user_id, **data}
        res = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.commit()
        return res

    async def list_case_studies(
        self, pagination: PaginationParams
    ) -> PaginatedResult[PortfolioCaseStudy]:
        return await self.repo.list(self.db, self.user_id, pagination)

    async def get_case_study(self, id: str) -> PortfolioCaseStudy:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Case study not found.')
        return res

    async def update_case_study(self, id: str, data: Dict[str, Any]) -> PortfolioCaseStudy:
        res = await self.repo.update(self.db, self.user_id, id, data)
        if not res:
            raise NotFoundError('Case study not found.')
        await self.db.commit()
        return res

    async def delete_case_study(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Case study not found.')
        await self.db.commit()
        return res


class ContentService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.repo = ContentRepository()
        self.ver_repo = ContentVersionRepository()

    async def create_content(self, data: Dict[str, Any]) -> ContentItem:
        obj_in = {"user_id": self.user_id, **data}
        item = await self.repo.create(self.db, obj_in_data=obj_in)
        await self.db.flush()

        ver_in = {
            "user_id": self.user_id,
            "content_id": item.id,
            "version_number": 1,
            "title": item.title,
            "body": item.body,
            "change_summary": "Initial content drafting",
        }
        await self.ver_repo.create(self.db, obj_in_data=ver_in)
        await self.db.commit()
        return item

    async def list_content(
        self, pagination: PaginationParams, content_type: Optional[str] = None
    ) -> PaginatedResult[ContentItem]:
        filters = {}
        if content_type:
            filters["content_type"] = content_type
        return await self.repo.list(self.db, self.user_id, pagination, **filters)

    async def update_content(self, id: str, data: Dict[str, Any]) -> ContentItem:
        existing = await self.repo.get_by_id(self.db, self.user_id, id)
        if not existing:
            raise NotFoundError("Content record not found.")

        change_summary = data.pop("change_summary", "Modified content body")
        new_ver_number = existing.current_version_number + 1
        data["current_version_number"] = new_ver_number

        updated = await self.repo.update(self.db, self.user_id, id, data)
        if not updated:
            raise NotFoundError("Failed to update content item.")

        await self.db.flush()

        ver_in = {
            "user_id": self.user_id,
            "content_id": id,
            "version_number": new_ver_number,
            "title": updated.title,
            "body": updated.body,
            "change_summary": change_summary,
        }
        await self.ver_repo.create(self.db, obj_in_data=ver_in)
        await self.db.commit()
        return updated

    async def list_versions(self, content_id: str) -> List[ContentVersion]:
        return await self.ver_repo.list_versions(self.db, self.user_id, content_id)

    async def get_content(self, id: str) -> ContentItem:
        res = await self.repo.get_by_id(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Content not found.')
        return res

    async def delete_content(self, id: str) -> bool:
        res = await self.repo.delete(self.db, self.user_id, id)
        if not res:
            raise NotFoundError('Content not found.')
        await self.db.commit()
        return res

