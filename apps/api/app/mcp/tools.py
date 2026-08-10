"""
MCP Domain Tools implementation reusing shared backend repositories and services.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PaginationParams
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


class MCPDomainTools:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.uid = _to_uuid(user_id)

    async def search_people(
        self, query: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
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
        try:
            memories, _ = await MemoriesRepository.list_memories(
                self.db, user_id=self.uid, category=category, limit=limit
            )
            results = []
            for m in memories:
                data = _serialize_model(m, "memory", "mcp://memory")
                if query:
                    text_corpus = f"{data.get('title', '')} {data.get('content', '')}".lower()
                    if query.lower() not in text_corpus:
                        continue
                results.append(data)
            return results
        except Exception:
            return []

    async def get_projects(
        self, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            repo = ProjectRepository()
            params = PaginationParams(limit=limit, offset=0)
            filters = {}
            if status:
                filters["status"] = status
            paginated = await repo.list(self.db, str(self.user_id), params, **filters)
            return [_serialize_model(p, "project", "mcp://projects") for p in paginated.items]
        except Exception:
            return []

    async def get_tasks(
        self, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            repo = TaskRepository()
            params = PaginationParams(limit=limit, offset=0)
            filters = {}
            if status:
                filters["status"] = status
            paginated = await repo.list(self.db, str(self.user_id), params, **filters)
            return [_serialize_model(t, "task", "mcp://tasks") for t in paginated.items]
        except Exception:
            return []

    async def get_relationship_history(
        self, person_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        try:
            interactions, _ = await InteractionsRepository.list_interactions(
                self.db, user_id=self.uid, person_id=_to_uuid(person_id), limit=limit
            )
            return [_serialize_model(i, "interaction", "mcp://interactions") for i in interactions]
        except Exception:
            return []

    async def get_calendar(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            meetings, _ = await MeetingsRepository.list_meetings(
                self.db, user_id=self.uid, limit=limit
            )
            return [_serialize_model(m, "meeting", "mcp://calendar") for m in meetings]
        except Exception:
            return []

    async def generate_linkedin_post(
        self, topic: str, style_tone: Optional[str] = "executive"
    ) -> Dict[str, Any]:
        memories = await self.search_memory(query=topic, limit=5)
        citations = [
            m.get("source_grounding", {}).get("citation_uri")
            for m in memories
            if m.get("source_grounding")
        ]
        insights = [m.get("title") or m.get("content", "")[:100] for m in memories]

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
        projects = await self.get_projects(limit=10)
        matched = next(
            (p for p in projects if project_name.lower() in p.get("name", "").lower()), None
        )

        title = matched.get("name", project_name) if matched else project_name
        return {
            "title": f"Case Study: {title}",
            "project_name": title,
            "role": "Founder / Product Lead",
            "problem_statement": f"Solving execution and scalability bottlenecks in {title}.",
            "responsibilities": [
                "AI Product Strategy",
                "Architecture Design",
                "Multi-Agent Systems Execution",
            ],
            "impact_metrics": ["Validated MVP launch", "Streamlined operation workflows"],
            "skills": ["AI Product Management", "System Architecture", "Leadership"],
            "status": "draft",
            "notice": "Staged draft mode - requires human review prior to portfolio export.",
        }

    async def generate_weekly_review(self) -> Dict[str, Any]:
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
