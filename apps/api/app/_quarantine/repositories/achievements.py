"""
Achievement Portfolio Repository
Module Owner: Agent 9
Enforces RLS isolation & evidence attachment tracking for verified founder claims.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class AchievementRepository:
    def __init__(self, db_client: Any):
        self.db = db_client
        self.table_name = "achievements"
        self.evidence_table = "achievement_evidence"

    async def get_by_id(self, user_id: str, achievement_id: str) -> Optional[Dict[str, Any]]:
        result = (
            await self.db.table(self.table_name)
            .select("*")
            .eq("id", achievement_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_achievements(
        self, user_id: str, venture_id: Optional[str] = None, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
        )

        if venture_id:
            query = query.eq("venture_id", venture_id)

        result = (
            await query.order("achievement_date", desc=True).limit(limit).offset(offset).execute()
        )
        return result.data or []

    async def create_achievement(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        evidence_items = data.pop("evidence_items", [])
        record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        result = await self.db.table(self.table_name).insert(record).execute()
        created = result.data[0] if result.data else record

        # Insert evidence items if present
        if evidence_items:
            for item in evidence_items:
                ev_record = {
                    "id": str(uuid4()),
                    "achievement_id": created["id"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    **item,
                }
                await self.db.table(self.evidence_table).insert(ev_record).execute()

        created["evidence_items"] = evidence_items
        return created

    async def update_achievement(
        self, user_id: str, achievement_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.table_name)
            .update(updates)
            .eq("id", achievement_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete_achievement(self, user_id: str, achievement_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.table_name)
            .update({"deleted_at": now_iso, "updated_at": now_iso})
            .eq("id", achievement_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return bool(result.data)
