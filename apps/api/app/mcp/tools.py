"""
MCP Domain Tools implementation reusing shared backend repositories and services.
Provides safe, user-scoped personal operating interface and Work Intelligence finalizer.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams
from app.jobs.index_queue import queue_index
from app.mcp.beta_tools import BetaMCPTools
from app.models.entities import (
    AuditLog,
    Decision,
    Interaction,
    Memory,
    Person,
    PortfolioCaseStudy,
    Project,
    Task,
    Venture,
)
from app.repositories.crm import CRMRepository
from app.repositories.interactions import InteractionsRepository
from app.repositories.meetings import MeetingsRepository
from app.repositories.memories import MemoriesRepository
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository


def _to_uuid(val: Any) -> Any:
    if isinstance(val, uuid.UUID) or val is None:
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError, AttributeError):
        return val


def _parse_iso_date(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


def _serialize_model(obj: Any, source_type: str, uri_prefix: str) -> Dict[str, Any]:
    if obj is None:
        return {}
    if hasattr(obj, "__dict__"):
        data = {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    elif isinstance(obj, dict):
        data = dict(obj)
    else:
        data = {"value": str(obj)}

    formatted: Dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, uuid.UUID):
            formatted[k] = str(v)
        elif isinstance(v, datetime):
            formatted[k] = v.isoformat()
        else:
            formatted[k] = v

    obj_id = str(formatted.get("id", "unknown"))
    formatted["source_grounding"] = {
        "origin_id": obj_id,
        "source_type": source_type,
        "citation_uri": f"{uri_prefix}/{obj_id}",
    }
    return formatted


def _parse_markdown_sections(text: str) -> Dict[str, List[str]]:
    """Parse unstructured session text or markdown notes into extracted intelligence buckets."""
    if not text:
        return {}
    lines = text.split("\n")
    sections: Dict[str, List[str]] = {
        "decisions": [],
        "tasks": [],
        "people": [],
        "findings": [],
        "research": [],
        "work_completed": [],
        "artifacts": [],
        "skills": [],
        "portfolio": [],
        "questions": [],
        "evidence": [],
    }
    current_key: Optional[str] = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower_line = stripped.lower()
        if lower_line.startswith("#"):
            header_title = lower_line.lstrip("#").strip()
            if "decision" in header_title:
                current_key = "decisions"
            elif any(k in header_title for k in ("task", "action", "todo", "next step")):
                current_key = "tasks"
            elif any(k in header_title for k in ("people", "person", "contact", "attendee")):
                current_key = "people"
            elif any(k in header_title for k in ("finding", "takeaway", "lesson", "insight")):
                current_key = "findings"
            elif any(k in header_title for k in ("research", "investigat", "benchmark")):
                current_key = "research"
            elif any(k in header_title for k in ("work completed", "progress", "accomplish", "done")):
                current_key = "work_completed"
            elif any(k in header_title for k in ("artifact", "deliverable", "file", "document", "pr")):
                current_key = "artifacts"
            elif "skill" in header_title:
                current_key = "skills"
            elif any(k in header_title for k in ("portfolio", "case study", "achievement")):
                current_key = "portfolio"
            elif any(k in header_title for k in ("question", "unresolved", "open question", "risk")):
                current_key = "questions"
            elif any(k in header_title for k in ("evidence", "source", "reference", "citation")):
                current_key = "evidence"
            else:
                current_key = None
            continue

        if current_key:
            cleaned_bullet = re.sub(r"^[-*•\d\.\)]+\s*", "", stripped).strip()
            if cleaned_bullet:
                sections[current_key].append(cleaned_bullet)

    return sections


# Public alias: app/mcp/extraction.py reuses this deterministic parser as its offline mode
# and as the fallback when Gemini inference fails.
parse_markdown_sections = _parse_markdown_sections




class MCPDomainTools(BetaMCPTools):
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = str(user_id)
        self.uid = _to_uuid(user_id)

    async def _emit_audit(
        self,
        event_type: str,
        target_entity: str,
        target_id: str,
        details: Dict[str, Any],
        request_id: str = "N/A",
    ) -> None:
        """Record structured audit log for state-modifying operations."""
        try:
            audit = AuditLog(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                event_type=event_type,
                target_entity=target_entity,
                target_id=str(target_id),
                details=details,
                timestamp=datetime.now(timezone.utc),
                request_id=request_id,
            )
            self.db.add(audit)
            await self.db.flush()
            queue_index(self.db, audit)
        except Exception:  # nosec B110
            pass

    # ==========================================
    # READ TOOLS
    # ==========================================

    async def search_people(
        self, query: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search CRM contacts scoped to current authenticated user."""
        try:
            people, _ = await CRMRepository.list_people(
                self.db, user_id=self.uid, q=query, limit=limit
            )
            return [_serialize_model(p, "person", "mcp://people") for p in people]
        except Exception:
            return []

    async def search_memory(
        self, query: Optional[str] = None, category: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search memories and founder notes scoped to current authenticated user."""
        try:
            memories, _ = await MemoriesRepository.list_memories(
                self.db, user_id=self.uid, category=category, limit=limit
            )
            results = []
            for m in memories:
                data = _serialize_model(m, "memory", "mcp://memory")
                if query:
                    text_corpus = f"{data.get('title', '')} {data.get('body', '')} {data.get('content', '')}".lower()
                    if query.lower() not in text_corpus:
                        continue
                results.append(data)
            return results
        except Exception:
            return []

    async def get_projects(
        self, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve user projects across ventures."""
        try:
            repo = ProjectRepository()
            params = PaginationParams(limit=limit, offset=0)
            filters = {}
            if status:
                filters["status"] = status
            paginated = await repo.list(self.db, self.user_id, params, **filters)
            return [_serialize_model(p, "project", "mcp://projects") for p in paginated.items]
        except Exception:
            return []

    async def get_tasks(
        self, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve user tasks."""
        try:
            repo = TaskRepository()
            params = PaginationParams(limit=limit, offset=0)
            filters = {}
            if status:
                filters["status"] = status
            paginated = await repo.list(self.db, self.user_id, params, **filters)
            return [_serialize_model(t, "task", "mcp://tasks") for t in paginated.items]
        except Exception:
            return []

    async def get_relationship_history(
        self, person_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve interaction timeline for a specific person profile in CRM."""
        try:
            interactions, _ = await InteractionsRepository.list_interactions(
                self.db, user_id=self.uid, person_id=_to_uuid(person_id), limit=limit
            )
            return [_serialize_model(i, "interaction", "mcp://interactions") for i in interactions]
        except Exception:
            return []

    async def get_calendar(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve scheduled meetings and calendar events."""
        try:
            meetings, _ = await MeetingsRepository.list_meetings(
                self.db, user_id=self.uid, limit=limit
            )
            return [_serialize_model(m, "meeting", "mcp://calendar") for m in meetings]
        except Exception:
            return []

    # ==========================================
    # WRITE TOOLS - SAFE ATOMIC MUTATIONS
    # ==========================================

    async def save_memory(
        self,
        title: str,
        content: str,
        category: Optional[str] = "note",
        tags: Optional[List[str]] = None,
        linked_venture_id: Optional[str] = None,
        linked_person_id: Optional[str] = None,
        importance: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save a new memory / note record for the authenticated user."""
        try:
            mem = Memory(
                id=uuid.uuid4(),
                user_id=self.uid,
                title=title,
                body=content,
                type=category or "note",
                tags=tags or [],
                importance=importance,
                linked_venture_id=_to_uuid(linked_venture_id),
                linked_person_id=_to_uuid(linked_person_id),
                meta=metadata or {},
                source="mcp_interface",
            )
            self.db.add(mem)
            await self.db.flush()
            queue_index(self.db, mem)
            await self.db.refresh(mem)
            await self._emit_audit(
                "mcp.memory.saved",
                "memory",
                str(mem.id),
                {"title": title, "category": category},
            )
            return _serialize_model(mem, "memory", "mcp://memory")
        except Exception as e:
            await self.db.rollback()
            raise e

    async def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        status: Optional[str] = "todo",
        priority: Optional[str] = "medium",
        due_date: Optional[str] = None,
        project_id: Optional[str] = None,
        venture_id: Optional[str] = None,
        person_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new task record with user scoping."""
        try:
            parsed_due = _parse_iso_date(due_date)
            task = Task(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                title=title,
                description=description,
                status=status or "todo",
                priority=priority or "medium",
                due_date=parsed_due,
                project_id=str(project_id) if project_id else None,
                venture_id=str(venture_id) if venture_id else None,
                person_id=str(person_id) if person_id else None,
                tags=tags or [],
                calendar_sync_metadata=metadata or {},
            )
            self.db.add(task)
            await self.db.flush()
            queue_index(self.db, task)
            await self.db.refresh(task)
            await self._emit_audit(
                "mcp.task.created",
                "task",
                str(task.id),
                {"title": title, "priority": priority, "status": task.status},
            )
            return _serialize_model(task, "task", "mcp://tasks")
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        completion_date: Optional[str] = None,
        project_id: Optional[str] = None,
        venture_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update an existing task owned by the authenticated user."""
        try:
            stmt = select(Task).where(
                Task.id == str(task_id),
                Task.user_id == self.user_id,
                Task.deleted_at.is_(None),
            )
            res = await self.db.execute(stmt)
            task = res.scalar_one_or_none()
            if not task:
                return {"error": "Task not found or access denied", "task_id": task_id}

            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if status is not None:
                task.status = status
                if status.lower() in ("completed", "done") and not completion_date and not task.completion_date:
                    task.completion_date = datetime.now(timezone.utc)
            if priority is not None:
                task.priority = priority
            if due_date is not None:
                task.due_date = _parse_iso_date(due_date)
            if completion_date is not None:
                task.completion_date = _parse_iso_date(completion_date)
            if project_id is not None:
                task.project_id = str(project_id)
            if venture_id is not None:
                task.venture_id = str(venture_id)
            if tags is not None:
                task.tags = tags

            task.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(task)
            await self._emit_audit(
                "mcp.task.updated", "task", str(task.id), {"updated_status": task.status}
            )
            return _serialize_model(task, "task", "mcp://tasks")
        except Exception as e:
            await self.db.rollback()
            raise e

    async def complete_task(
        self, task_id: str, completion_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark a user task as completed with completion metadata."""
        try:
            stmt = select(Task).where(
                Task.id == str(task_id),
                Task.user_id == self.user_id,
                Task.deleted_at.is_(None),
            )
            res = await self.db.execute(stmt)
            task = res.scalar_one_or_none()
            if not task:
                return {"error": "Task not found or access denied", "task_id": task_id}

            task.status = "completed"
            task.completion_date = datetime.now(timezone.utc)
            if completion_notes:
                notes_prefix = f"\n\n[Completion Notes: {completion_notes}]"
                task.description = (task.description or "") + notes_prefix
            task.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(task)
            await self._emit_audit(
                "mcp.task.completed", "task", str(task.id), {"completion_notes": completion_notes}
            )
            return _serialize_model(task, "task", "mcp://tasks")
        except Exception as e:
            await self.db.rollback()
            raise e

    async def create_person(
        self,
        name: str,
        role: Optional[str] = None,
        company: Optional[str] = None,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        relationship_type: Optional[str] = "contact",
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        organization_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new CRM contact for the authenticated user with intelligent deduplication.
        If a matching contact exists by email or exact name, returns deduplicated existing record.
        """
        try:
            # Deduplication Check
            stmt = select(Person).where(Person.user_id == self.uid, Person.deleted_at.is_(None))
            res = await self.db.execute(stmt)
            existing_people = list(res.scalars().all())

            clean_name = name.strip()
            clean_email = email.strip().lower() if email else None

            matched: Optional[Person] = None
            for p in existing_people:
                if clean_email and p.email and p.email.strip().lower() == clean_email:
                    matched = p
                    break
                if p.name and p.name.strip().lower() == clean_name.lower():
                    matched = p
                    break

            if matched:
                # Merge tags and metadata
                merged_tags = list(set((matched.tags or []) + (tags or [])))
                matched.tags = merged_tags
                if role and not matched.role:
                    matched.role = role
                if company and not matched.company:
                    matched.company = company
                if notes and notes not in (matched.notes or ""):
                    matched.notes = (matched.notes or "") + f"\n{notes}".strip()
                matched.updated_at = datetime.now(timezone.utc)
                await self.db.flush()
                await self.db.refresh(matched)
                await self._emit_audit(
                    "mcp.person.deduplicated_matched",
                    "person",
                    str(matched.id),
                    {"name": matched.name, "deduplicated": True},
                )
                res_dict = _serialize_model(matched, "person", "mcp://people")
                res_dict["deduplicated"] = True
                return res_dict

            person = Person(
                id=uuid.uuid4(),
                user_id=self.uid,
                organization_id=_to_uuid(organization_id),
                name=clean_name,
                role=role,
                company=company,
                industry=industry,
                location=location,
                email=email,
                phone=phone,
                linkedin_url=linkedin_url,
                relationship_type=relationship_type or "contact",
                notes=notes,
                tags=tags or [],
                meta=metadata or {},
            )
            self.db.add(person)
            await self.db.flush()
            queue_index(self.db, person)
            await self.db.refresh(person)
            await self._emit_audit(
                "mcp.person.created", "person", str(person.id), {"name": clean_name}
            )
            res_dict = _serialize_model(person, "person", "mcp://people")
            res_dict["deduplicated"] = False
            return res_dict
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update_person(
        self,
        person_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        company: Optional[str] = None,
        industry: Optional[str] = None,
        location: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        relationship_type: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update contact profile owned by current authenticated user."""
        try:
            stmt = select(Person).where(
                Person.id == _to_uuid(person_id),
                Person.user_id == self.uid,
                Person.deleted_at.is_(None),
            )
            res = await self.db.execute(stmt)
            person = res.scalar_one_or_none()
            if not person:
                return {"error": "Person not found or access denied", "person_id": person_id}

            if name is not None:
                person.name = name
            if role is not None:
                person.role = role
            if company is not None:
                person.company = company
            if industry is not None:
                person.industry = industry
            if location is not None:
                person.location = location
            if email is not None:
                person.email = email
            if phone is not None:
                person.phone = phone
            if linkedin_url is not None:
                person.linkedin_url = linkedin_url
            if relationship_type is not None:
                person.relationship_type = relationship_type
            if notes is not None:
                person.notes = notes
            if tags is not None:
                person.tags = tags
            if metadata is not None:
                person.meta = metadata

            person.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(person)
            await self._emit_audit(
                "mcp.person.updated", "person", str(person.id), {"name": person.name}
            )
            return _serialize_model(person, "person", "mcp://people")
        except Exception as e:
            await self.db.rollback()
            raise e

    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        venture_id: Optional[str] = None,
        status: Optional[str] = "in_progress",
        priority: Optional[str] = "medium",
        progress: Optional[int] = 0,
        target_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create project with user scoping and duplicate prevention."""
        try:
            clean_name = name.strip()
            stmt = select(Project).where(
                Project.user_id == self.user_id,
                func.lower(Project.name) == clean_name.lower(),
                Project.deleted_at.is_(None),
            )
            res = await self.db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                res_dict = _serialize_model(existing, "project", "mcp://projects")
                res_dict["deduplicated"] = True
                return res_dict

            proj = Project(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                venture_id=str(venture_id) if venture_id else None,
                name=clean_name,
                description=description,
                status=status or "in_progress",
                priority=priority or "medium",
                progress=progress or 0,
                target_date=_parse_iso_date(target_date),
            )
            self.db.add(proj)
            await self.db.flush()
            queue_index(self.db, proj)
            await self.db.refresh(proj)
            await self._emit_audit(
                "mcp.project.created", "project", str(proj.id), {"name": clean_name}
            )
            res_dict = _serialize_model(proj, "project", "mcp://projects")
            res_dict["deduplicated"] = False
            return res_dict
        except Exception as e:
            await self.db.rollback()
            raise e

    async def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        venture_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        progress: Optional[int] = None,
        target_date: Optional[str] = None,
        completion_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update existing project for authenticated user."""
        try:
            stmt = select(Project).where(
                Project.id == str(project_id),
                Project.user_id == self.user_id,
                Project.deleted_at.is_(None),
            )
            res = await self.db.execute(stmt)
            proj = res.scalar_one_or_none()
            if not proj:
                return {"error": "Project not found or access denied", "project_id": project_id}

            if name is not None:
                proj.name = name
            if description is not None:
                proj.description = description
            if venture_id is not None:
                proj.venture_id = str(venture_id)
            if status is not None:
                proj.status = status
            if priority is not None:
                proj.priority = priority
            if progress is not None:
                proj.progress = progress
            if target_date is not None:
                proj.target_date = _parse_iso_date(target_date)
            if completion_date is not None:
                proj.completion_date = _parse_iso_date(completion_date)

            proj.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(proj)
            await self._emit_audit(
                "mcp.project.updated", "project", str(proj.id), {"name": proj.name}
            )
            return _serialize_model(proj, "project", "mcp://projects")
        except Exception as e:
            await self.db.rollback()
            raise e

    async def save_decision(
        self,
        decision: str,
        context: Optional[str] = None,
        rationale: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
        expected_impact: Optional[str] = None,
        project_id: Optional[str] = None,
        venture_id: Optional[str] = None,
        supporting_people: Optional[List[str]] = None,
        supporting_documents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Record strategic or technical decision with context and rationale."""
        try:
            dec = Decision(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                title=(decision or "").strip()[:255] or "Untitled decision",
                decision=decision,
                context=context or decision,
                rationale=rationale,
                alternatives=alternatives or [],
                expected_impact=expected_impact,
                project_id=str(project_id) if project_id else None,
                venture_id=str(venture_id) if venture_id else None,
                supporting_people=supporting_people or [],
                supporting_documents=supporting_documents or [],
            )
            self.db.add(dec)
            await self.db.flush()
            queue_index(self.db, dec)
            await self.db.refresh(dec)
            await self._emit_audit(
                "mcp.decision.saved", "decision", str(dec.id), {"decision": decision[:100]}
            )
            return _serialize_model(dec, "decision", "mcp://decisions")
        except Exception as e:
            await self.db.rollback()
            raise e

    async def save_work_session(
        self,
        title: str,
        summary: Optional[str] = None,
        detailed_notes: Optional[str] = None,
        project_id: Optional[str] = None,
        venture_id: Optional[str] = None,
        person_id: Optional[str] = None,
        interaction_type: Optional[str] = "work_session",
        key_takeaways: Optional[List[str]] = None,
        next_actions: Optional[List[str]] = None,
        client_request_id: Optional[str] = None,
        provider: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save a work session interaction with user isolation and audit tracking."""
        try:
            meta = dict(metadata or {})
            if client_request_id:
                meta["client_request_id"] = client_request_id
            if provider:
                meta["provider"] = provider

            interaction = Interaction(
                id=uuid.uuid4(),
                user_id=self.uid,
                person_id=_to_uuid(person_id),
                venture_id=_to_uuid(venture_id),
                project_id=_to_uuid(project_id),
                interaction_type=interaction_type or "work_session",
                title=title,
                summary=summary or "",
                detailed_notes=detailed_notes or "",
                date=datetime.now(timezone.utc),
                key_takeaways=key_takeaways or [],
                next_actions=next_actions or [],
                meta=meta,
            )
            self.db.add(interaction)
            await self.db.flush()
            queue_index(self.db, interaction)
            await self.db.refresh(interaction)
            await self._emit_audit(
                "mcp.work_session.saved", "interaction", str(interaction.id), {"title": title}
            )
            return _serialize_model(interaction, "interaction", "mcp://sessions")
        except Exception as e:
            await self.db.rollback()
            raise e

    # ==========================================
    # FINALIZE_WORK_SESSION - CORE WORK INTELLIGENCE
    # ==========================================

    async def finalize_work_session(
        self,
        provider: Optional[str] = "mcp_client",
        conversation_reference: Optional[str] = None,
        session_reference: Optional[str] = None,
        client_request_id: Optional[str] = None,
        summary: Optional[str] = None,
        session_payload: Optional[Dict[str, Any]] = None,
        venture_hint: Optional[str] = None,
        project_hint: Optional[str] = None,
        title: Optional[str] = None,
        objective: Optional[str] = None,
        work_completed: Optional[List[str]] = None,
        research: Optional[Any] = None,
        findings: Optional[List[str]] = None,
        decisions: Optional[List[Any]] = None,
        rationale: Optional[str] = None,
        rejected_alternatives: Optional[List[str]] = None,
        tasks: Optional[List[Any]] = None,
        people_mentioned: Optional[List[Any]] = None,
        organizations_mentioned: Optional[List[Any]] = None,
        evidence: Optional[List[Any]] = None,
        source_references: Optional[List[str]] = None,
        artifacts: Optional[List[Any]] = None,
        skills_demonstrated: Optional[List[str]] = None,
        portfolio_candidates: Optional[List[Any]] = None,
        unresolved_questions: Optional[List[str]] = None,
        commitments: Optional[List[str]] = None,
        extraction: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Low-friction, comprehensive Work Intelligence session finalizer.
        Extracts tasks, decisions, people, findings, and artifacts; performs deduplication;
        attaches provenance to all records; supports idempotency replay; and records audit telemetry.
        """
        try:
            # 1. Idempotency Check
            idempotency_key = client_request_id or session_reference or conversation_reference
            if idempotency_key:
                stmt = select(Interaction).where(
                    Interaction.user_id == self.uid,
                    Interaction.interaction_type == "work_session",
                    Interaction.deleted_at.is_(None),
                )
                res = await self.db.execute(stmt)
                existing_sessions = list(res.scalars().all())
                for s in existing_sessions:
                    s_meta = s.meta if isinstance(s.meta, dict) else {}
                    if (
                        s_meta.get("client_request_id") == idempotency_key
                        or s_meta.get("session_reference") == idempotency_key
                        or s_meta.get("conversation_reference") == idempotency_key
                    ):
                        return {
                            "status": "finalized",
                            "idempotent_replayed": True,
                            "session_id": str(s.id),
                            "session_grounding": f"mcp://sessions/{s.id}",
                            "message": "Idempotent request: Work session already finalized.",
                            "resolved_context": s_meta.get("resolved_context", {}),
                            "created_records": s_meta.get("created_records", {}),
                            "extracted_intelligence": s_meta.get("extracted_intelligence", {}),
                            "provenance": {
                                "session_uri": f"mcp://sessions/{s.id}",
                                "provider": s_meta.get("provider", provider),
                                "client_request_id": idempotency_key,
                                "timestamp": s.created_at.isoformat() if s.created_at else None,
                                "extraction": s_meta.get("extraction", {}),
                            },
                        }

            # 2. Merge inputs from session_payload & unstructured summary text
            payload = dict(session_payload or {})
            raw_summary = summary or payload.get("summary") or ""
            parsed_sections = _parse_markdown_sections(raw_summary)

            resolved_title = (
                title
                or payload.get("title")
                or (f"Work Session: {project_hint}" if project_hint else "Founder Work Session")
            )
            resolved_objective = objective or payload.get("objective") or ""
            resolved_work_completed = (
                work_completed
                or payload.get("work_completed")
                or parsed_sections.get("work_completed")
                or []
            )

            # Decisions
            raw_decisions = decisions or payload.get("decisions") or parsed_sections.get("decisions") or []
            # Tasks
            raw_tasks = tasks or payload.get("tasks") or parsed_sections.get("tasks") or []
            # People
            raw_people = (
                people_mentioned
                or payload.get("people_mentioned")
                or parsed_sections.get("people")
                or []
            )
            # Findings
            resolved_findings = (
                findings
                or payload.get("findings")
                or parsed_sections.get("findings")
                or []
            )
            # Research
            raw_research = research or payload.get("research") or parsed_sections.get("research") or []
            resolved_research = raw_research if isinstance(raw_research, list) else [str(raw_research)]
            # Evidence
            resolved_evidence = evidence or payload.get("evidence") or parsed_sections.get("evidence") or []
            # Sources
            resolved_sources = source_references or payload.get("source_references") or []
            # Artifacts
            resolved_artifacts = artifacts or payload.get("artifacts") or parsed_sections.get("artifacts") or []
            # Skills
            resolved_skills = (
                skills_demonstrated
                or payload.get("skills_demonstrated")
                or parsed_sections.get("skills")
                or []
            )
            # Portfolio candidates
            resolved_portfolio = (
                portfolio_candidates
                or payload.get("portfolio_candidates")
                or parsed_sections.get("portfolio")
                or []
            )
            # Commitments made during the session
            resolved_commitments = (
                commitments or payload.get("commitments") or []
            )
            # Organizations referenced (stored as session provenance, not created as records)
            resolved_organizations = (
                organizations_mentioned or payload.get("organizations_mentioned") or []
            )
            # Unresolved questions
            resolved_questions = (
                unresolved_questions
                or payload.get("unresolved_questions")
                or parsed_sections.get("questions")
                or []
            )

            # 3. Project & Venture Resolution with Deduplication & Unresolved-Link Handling
            proj_hint = project_hint or payload.get("project_hint") or payload.get("project_name")
            vent_hint = venture_hint or payload.get("venture_hint") or payload.get("venture_name")

            resolved_project_id: Optional[str] = None
            resolved_project_name: Optional[str] = None
            resolved_venture_id: Optional[str] = None
            resolved_venture_name: Optional[str] = None
            unresolved_links: List[Dict[str, Any]] = []

            # Match Project
            stmt_proj = select(Project).where(
                Project.user_id == self.user_id, Project.deleted_at.is_(None)
            )
            res_proj = await self.db.execute(stmt_proj)
            user_projects = list(res_proj.scalars().all())

            if proj_hint:
                clean_p_hint = str(proj_hint).strip().lower()
                matched_proj = next(
                    (
                        p
                        for p in user_projects
                        if p.name.strip().lower() == clean_p_hint
                        or clean_p_hint in p.name.strip().lower()
                        or p.name.strip().lower() in clean_p_hint
                    ),
                    None,
                )
                if matched_proj:
                    resolved_project_id = str(matched_proj.id)
                    resolved_project_name = matched_proj.name
                    if matched_proj.venture_id and not vent_hint:
                        resolved_venture_id = str(matched_proj.venture_id)
                else:
                    unresolved_links.append(
                        {
                            "type": "project",
                            "hint": proj_hint,
                            "reason": "No matching active project in workspace; phantom project creation avoided.",
                        }
                    )

            # Match Venture
            stmt_vent = select(Venture).where(
                Venture.user_id == self.user_id, Venture.deleted_at.is_(None)
            )
            res_vent = await self.db.execute(stmt_vent)
            user_ventures = list(res_vent.scalars().all())

            if vent_hint:
                clean_v_hint = str(vent_hint).strip().lower()
                matched_vent = next(
                    (
                        v
                        for v in user_ventures
                        if v.name.strip().lower() == clean_v_hint
                        or v.slug.strip().lower() == clean_v_hint
                        or clean_v_hint in v.name.strip().lower()
                    ),
                    None,
                )
                if matched_vent:
                    resolved_venture_id = str(matched_vent.id)
                    resolved_venture_name = matched_vent.name
                else:
                    unresolved_links.append(
                        {
                            "type": "venture",
                            "hint": vent_hint,
                            "reason": "No matching active venture in workspace; phantom venture creation avoided.",
                        }
                    )

            # 4. Create Canonical Session Interaction Record
            session_id = uuid.uuid4()
            session_uri = f"mcp://sessions/{session_id}"

            session_meta: Dict[str, Any] = {
                "client_request_id": idempotency_key,
                "session_reference": session_reference or conversation_reference,
                "conversation_reference": conversation_reference,
                "provider": provider or "mcp_client",
                "objective": resolved_objective,
                "work_completed": resolved_work_completed,
                "research": resolved_research,
                "findings": resolved_findings,
                "evidence": resolved_evidence,
                "source_references": resolved_sources,
                "artifacts": resolved_artifacts,
                "skills_demonstrated": resolved_skills,
                "portfolio_candidates": resolved_portfolio,
                "unresolved_questions": resolved_questions,
                "commitments": resolved_commitments,
                "organizations_mentioned": resolved_organizations,
                "unresolved_links": unresolved_links,
                # How the buckets above were produced (AI vs deterministic parse). Written by
                # the MCP tool layer, which extracts before this transaction is opened.
                "extraction": dict(extraction or {}),
            }

            session_record = Interaction(
                id=session_id,
                user_id=self.uid,
                project_id=_to_uuid(resolved_project_id),
                venture_id=_to_uuid(resolved_venture_id),
                interaction_type="work_session",
                title=resolved_title,
                summary=raw_summary,
                detailed_notes=raw_summary,
                date=datetime.now(timezone.utc),
                key_takeaways=resolved_findings,
                commitments=[
                    c if isinstance(c, str) else str(c) for c in resolved_commitments
                ],
                next_actions=[
                    t if isinstance(t, str) else t.get("title", "") for t in raw_tasks
                ][:10],
                meta=session_meta,
            )
            self.db.add(session_record)
            await self.db.flush()
            queue_index(self.db, session_record)

            # 5. Extract & Create Canonical Decisions
            created_decisions: List[Dict[str, Any]] = []
            for item in raw_decisions:
                if isinstance(item, str):
                    d_text = item
                    d_context = resolved_objective or d_text
                    d_rationale = rationale or "Decided during work session."
                    d_alts = rejected_alternatives or []
                elif isinstance(item, dict):
                    d_text = item.get("decision") or item.get("title") or "Architectural decision"
                    d_context = item.get("context") or resolved_objective or d_text
                    d_rationale = item.get("rationale") or rationale or "Decided during work session."
                    d_alts = item.get("rejected_alternatives") or item.get("alternatives") or []
                else:
                    continue

                decision_obj = Decision(
                    id=str(uuid.uuid4()),
                    user_id=self.user_id,
                    title=(d_text or "").strip()[:255] or "Untitled decision",
                    project_id=resolved_project_id,
                    venture_id=resolved_venture_id,
                    context=d_context,
                    decision=d_text,
                    rationale=d_rationale,
                    alternatives=d_alts,
                    supporting_documents=[session_uri],
                )
                self.db.add(decision_obj)
                await self.db.flush()
                queue_index(self.db, decision_obj)
                created_decisions.append(_serialize_model(decision_obj, "decision", "mcp://decisions"))

            # 6. Extract & Create Canonical Tasks (with deduplication)
            created_tasks: List[Dict[str, Any]] = []
            stmt_t = select(Task).where(
                Task.user_id == self.user_id,
                Task.status != "completed",
                Task.deleted_at.is_(None),
            )
            res_t = await self.db.execute(stmt_t)
            open_tasks = list(res_t.scalars().all())

            for item in raw_tasks:
                if isinstance(item, str):
                    t_title = item
                    t_desc = f"Extracted from {resolved_title}"
                    t_priority = "medium"
                    t_due = None
                elif isinstance(item, dict):
                    t_title = item.get("title") or item.get("name") or "Action Item"
                    t_desc = item.get("description") or f"Extracted from {resolved_title}"
                    t_priority = item.get("priority") or "medium"
                    t_due = _parse_iso_date(item.get("due_date"))
                else:
                    continue

                # Check existing duplicate open task
                existing_t = next(
                    (
                        ot
                        for ot in open_tasks
                        if ot.title.strip().lower() == t_title.strip().lower()
                        and (ot.project_id == resolved_project_id or not resolved_project_id)
                    ),
                    None,
                )
                if existing_t:
                    task_ser = _serialize_model(existing_t, "task", "mcp://tasks")
                    task_ser["deduplicated"] = True
                    created_tasks.append(task_ser)
                    continue

                task_obj = Task(
                    id=str(uuid.uuid4()),
                    user_id=self.user_id,
                    project_id=resolved_project_id,
                    venture_id=resolved_venture_id,
                    title=t_title,
                    description=t_desc,
                    status="todo",
                    priority=t_priority,
                    due_date=t_due,
                    calendar_sync_metadata={
                        "origin_session_id": str(session_id),
                        "origin_session_uri": session_uri,
                        "provider": provider or "mcp_client",
                    },
                )
                self.db.add(task_obj)
                await self.db.flush()
                queue_index(self.db, task_obj)
                task_ser = _serialize_model(task_obj, "task", "mcp://tasks")
                task_ser["deduplicated"] = False
                created_tasks.append(task_ser)

            # 7. Extract & Match/Create People
            created_people: List[Dict[str, Any]] = []
            for item in raw_people:
                if isinstance(item, str):
                    p_name = item
                    p_role = None
                    p_comp = None
                elif isinstance(item, dict):
                    p_name = item.get("name") or "Contact"
                    p_role = item.get("role")
                    p_comp = item.get("company")
                else:
                    continue

                person_res = await self.create_person(
                    name=p_name,
                    role=p_role,
                    company=p_comp,
                    notes=f"Mentioned in work session {session_uri}",
                )
                created_people.append(person_res)

            # 8. Create Finding / Lesson Memories
            created_memories: List[Dict[str, Any]] = []
            for finding_text in resolved_findings:
                if not finding_text:
                    continue
                mem = Memory(
                    id=uuid.uuid4(),
                    user_id=self.uid,
                    title=f"Finding: {finding_text[:60]}",
                    body=finding_text,
                    type="lesson",
                    related_projects=[resolved_project_id] if resolved_project_id else [],
                    linked_venture_id=_to_uuid(resolved_venture_id),
                    source=f"work_session:{session_id}",
                    meta={"origin_session_id": str(session_id), "session_uri": session_uri},
                )
                self.db.add(mem)
                await self.db.flush()
                queue_index(self.db, mem)
                created_memories.append(_serialize_model(mem, "memory", "mcp://memory"))

            # 9. Stage Portfolio / Case Study Candidates (Draft-Safe Mode)
            staged_portfolio: List[Dict[str, Any]] = []
            for cand in resolved_portfolio:
                c_title = (
                    cand.get("title")
                    if isinstance(cand, dict)
                    else f"Case Study Candidate: {resolved_project_name or resolved_title}"
                )
                c_problem = cand.get("problem_statement") if isinstance(cand, dict) else str(cand)
                case_study = PortfolioCaseStudy(
                    id=str(uuid.uuid4()),
                    user_id=self.user_id,
                    title=c_title,
                    project_name=resolved_project_name or resolved_title,
                    role="Founder / Lead Engineer",
                    problem_statement=c_problem,
                    solution_details="\n".join(f"- {w}" for w in resolved_work_completed) or "Work session deliverables.",
                    metrics_impact="\n".join(f"- {f}" for f in resolved_findings) or "Validated solution.",
                    skills_demonstrated=resolved_skills,
                    is_ai_generated=True,
                )
                self.db.add(case_study)
                await self.db.flush()
                queue_index(self.db, case_study)
                staged_portfolio.append(
                    {
                        "id": str(case_study.id),
                        "title": case_study.title,
                        "status": "draft",
                        "notice": "Staged draft mode - requires human review prior to publication.",
                    }
                )

            # 10. Summary and Telemetry
            created_summary = {
                "session": {"id": str(session_id), "title": resolved_title},
                "decisions": created_decisions,
                "tasks": created_tasks,
                "people": created_people,
                "memories": created_memories,
                "portfolio_candidates": staged_portfolio,
            }

            extracted_intel = {
                "objective": resolved_objective,
                "work_completed": resolved_work_completed,
                "research": resolved_research,
                "findings": resolved_findings,
                "evidence": resolved_evidence,
                "source_references": resolved_sources,
                "artifacts": resolved_artifacts,
                "skills_demonstrated": resolved_skills,
                "unresolved_questions": resolved_questions,
                "commitments": resolved_commitments,
                "organizations_mentioned": resolved_organizations,
            }

            resolved_ctx = {
                "project_id": resolved_project_id,
                "project_name": resolved_project_name,
                "venture_id": resolved_venture_id,
                "venture_name": resolved_venture_name,
                "unresolved_links": unresolved_links,
            }

            # Update session meta with finalized summary
            session_meta["created_records"] = created_summary
            session_meta["extracted_intelligence"] = extracted_intel
            session_meta["resolved_context"] = resolved_ctx
            session_record.meta = session_meta
            await self.db.flush()
            await self.db.refresh(session_record)

            await self._emit_audit(
                "mcp.work_session.finalized",
                "interaction",
                str(session_id),
                {
                    "title": resolved_title,
                    "records_created": {
                        "decisions": len(created_decisions),
                        "tasks": len(created_tasks),
                        "people": len(created_people),
                        "memories": len(created_memories),
                        "portfolio_staged": len(staged_portfolio),
                    },
                    "idempotency_key": idempotency_key,
                },
            )

            return {
                "status": "finalized",
                "idempotent_replayed": False,
                "session_id": str(session_id),
                "session_grounding": session_uri,
                "resolved_context": resolved_ctx,
                "created_records": created_summary,
                "extracted_intelligence": extracted_intel,
                "provenance": {
                    "session_uri": session_uri,
                    "provider": provider or "mcp_client",
                    "client_request_id": idempotency_key,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "extraction": dict(extraction or {}),
                },
            }
        except Exception as e:
            await self.db.rollback()
            raise e

    # ==========================================
    # GENERATIVE DRAFTING TOOLS (PRESERVED)
    # ==========================================

    async def generate_linkedin_post(
        self, topic: str, style_tone: Optional[str] = "executive"
    ) -> Dict[str, Any]:
        """Synthesize draft LinkedIn post with review notice."""
        memories = await self.search_memory(query=topic, limit=5)
        citations = [
            m.get("source_grounding", {}).get("citation_uri")
            for m in memories
            if m.get("source_grounding")
        ]
        insights = [m.get("title") or m.get("body", "")[:100] for m in memories]

        draft_content = f"🚀 Thoughts on {topic} ({style_tone or 'executive'} perspective):\n\n"
        if insights:
            draft_content += "Key lessons from recent founder experiences:\n" + "\n".join(
                f"• {i}" for i in insights[:3]
            )
        else:
            draft_content += "Exploring strategic innovation, founder execution velocity, and disciplined product management."

        draft_content += "\n\n#BuildingInPublic #AIProductManagement #Founder #SecondBrain"

        return {
            "title": f"LinkedIn Draft: {topic}",
            "content": draft_content,
            "tone_applied": style_tone,
            "grounding_citations": citations,
            "status": "draft",
            "notice": "Staged draft mode - requires human review prior to publication.",
        }

    async def generate_case_study(self, project_name: str) -> Dict[str, Any]:
        """Synthesize staged portfolio case study draft."""
        projects = await self.get_projects(limit=10)
        matched = next(
            (p for p in projects if project_name.lower() in p.get("name", "").lower()), None
        )

        if not matched:
            return {"status": "insufficient_evidence", "notice": "No matching project found. Save project evidence first."}
        return {"title": f"Case Study: {matched['name']}", "project_name": matched['name'],
                "problem_statement": matched.get('description'), "impact_metrics": [], "skills": [],
                "source_ids": [matched['id']], "status": "evidence_outline",
                "notice": "Project record only. Role, actions, skills and impact need supporting evidence and review."}

    async def generate_weekly_review(self) -> Dict[str, Any]:
        """Synthesize weekly founder executive review."""
        tasks = await self.get_tasks(limit=50)
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        pending_tasks = [t for t in tasks if t.get("status") != "completed"]

        return {
            "review_period": datetime.utcnow().strftime("%Y-W%W"),
            "completed_count": len(completed_tasks),
            "pending_count": len(pending_tasks),
            "key_achievements": [t.get("title") for t in completed_tasks[:5]],
            "upcoming_focus": [t.get("title") for t in pending_tasks[:5]],
            "ai_coaching_insight": "Maintain steady execution momentum. Focus on closing high-priority bottlenecks first.",
            "status": "generated",
        }
