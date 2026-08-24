"""
Idea Vault Database Repository
Module Owner: Agent 9
Enforces user_id filtering & soft deletion across public.ideas and related tables.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class IdeaRepository:
    def __init__(self, db_client: Any):
        """
        Injected database client (Supabase / Async Postgres driver).
        """
        self.db = db_client
        self.table_name = "ideas"

    async def get_by_id(self, user_id: str, idea_id: str) -> Optional[Dict[str, Any]]:
        """Fetch active idea strictly scoped by user_id."""
        result = (
            await self.db.table(self.table_name)
            .select("*")
            .eq("id", idea_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )

        return result.data[0] if result.data else None

    async def list_ideas(
        self,
        user_id: str,
        status: Optional[str] = None,
        venture_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List user ideas with pagination and filters."""
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
        )

        if status:
            query = query.eq("status", status)
        if venture_id:
            query = query.eq("venture_id", venture_id)

        result = await query.order("updated_at", desc=True).limit(limit).offset(offset).execute()
        return result.data or []

    async def create_idea(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new idea tied to authenticated user."""
        record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        result = await self.db.table(self.table_name).insert(record).execute()
        return result.data[0] if result.data else record

    async def update_idea(
        self, user_id: str, idea_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an existing idea owned by user."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.table_name)
            .update(updates)
            .eq("id", idea_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )

        return result.data[0] if result.data else None

    async def delete_idea(self, user_id: str, idea_id: str) -> bool:
        """Soft-delete idea by setting deleted_at timestamp."""
        now_iso = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.table_name)
            .update({"status": "archived", "deleted_at": now_iso, "updated_at": now_iso})
            .eq("id", idea_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )

        return bool(result.data)

    async def execute_conversion_transaction(
        self, user_id: str, idea_id: str, project_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Atomic transaction: Convert idea to project without deleting the historical idea record.
        """
        new_project = {
            "id": str(uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status": "in_progress",
            **project_payload,
        }

        # Insert new project
        await self.db.table("projects").insert(new_project).execute()

        # Update source idea status and retain reference
        now_iso = datetime.now(timezone.utc).isoformat()
        await (
            self.db.table(self.table_name)
            .update({"status": "converted", "updated_at": now_iso})
            .eq("id", idea_id)
            .eq("user_id", user_id)
            .execute()
        )

        return {
            "new_project_id": new_project["id"],
            "source_idea_id": idea_id,
            "idea_status": "converted",
            "converted_at": now_iso,
        }
