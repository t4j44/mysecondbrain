"""
Portfolio Case Studies Repository
Module Owner: Agent 9
Enforces RLS isolation for executive presentation career proof documents.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class PortfolioRepository:
    def __init__(self, db_client: Any):
        self.db = db_client
        self.table_name = "portfolio_case_studies"

    async def get_by_id(self, user_id: str, case_study_id: str) -> Optional[Dict[str, Any]]:
        result = (
            await self.db.table(self.table_name)
            .select("*")
            .eq("id", case_study_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_case_studies(
        self, user_id: str, target_role: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
        )

        if target_role:
            query = query.eq("target_role", target_role)

        result = await query.order("updated_at", desc=True).limit(limit).offset(offset).execute()
        return result.data or []

    async def create_case_study(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        result = await self.db.table(self.table_name).insert(record).execute()
        return result.data[0] if result.data else record

    async def update_case_study(
        self, user_id: str, case_study_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.table_name)
            .update(updates)
            .eq("id", case_study_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete_case_study(self, user_id: str, case_study_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.table_name)
            .update({"deleted_at": now_iso, "updated_at": now_iso})
            .eq("id", case_study_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return bool(result.data)
