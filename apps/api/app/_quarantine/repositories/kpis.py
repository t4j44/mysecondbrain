"""
Life KPI System Repository
Module Owner: Agent 9
Enforces historical immutability of KPI entries & strict user_id scoping.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class KPIRepository:
    def __init__(self, db_client: Any):
        self.db = db_client
        self.def_table = "kpi_definitions"
        self.entry_table = "kpi_entries"

    # --- KPI DEFINITIONS ---
    async def get_kpi(self, user_id: str, kpi_id: str) -> Optional[Dict[str, Any]]:
        result = (
            await self.db.table(self.def_table)
            .select("*")
            .eq("id", kpi_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_kpis(
        self, user_id: str, category: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = (
            self.db.table(self.def_table)
            .select("*")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
        )

        if category:
            query = query.eq("category", category)

        result = await query.order("created_at", desc=False).limit(limit).offset(offset).execute()
        return result.data or []

    async def create_kpi(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "current_value": 0.0,
            **data,
        }
        result = await self.db.table(self.def_table).insert(record).execute()
        return result.data[0] if result.data else record

    async def update_kpi(
        self, user_id: str, kpi_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Updates definition without modifying past entries."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.def_table)
            .update(updates)
            .eq("id", kpi_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def delete_kpi(self, user_id: str, kpi_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.def_table)
            .update({"deleted_at": now_iso, "updated_at": now_iso})
            .eq("id", kpi_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return bool(result.data)

    # --- KPI ENTRIES ---
    async def create_entry(self, user_id: str, kpi_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        entry_record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "kpi_id": kpi_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **data,
        }
        result = await self.db.table(self.entry_table).insert(entry_record).execute()

        # Automatically update parent definition current_value with latest check-in value
        await (
            self.db.table(self.def_table)
            .update(
                {
                    "current_value": data["recorded_value"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", kpi_id)
            .eq("user_id", user_id)
            .execute()
        )

        return result.data[0] if result.data else entry_record

    async def list_entries(
        self, user_id: str, kpi_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        result = (
            await self.db.table(self.entry_table)
            .select("*")
            .eq("kpi_id", kpi_id)
            .eq("user_id", user_id)
            .order("recording_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
