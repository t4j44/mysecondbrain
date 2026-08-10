"""
AI Content Engine Repository & Version Tracking
Module Owner: Agent 9
Manages content items and immutable revision rows in public.content_versions.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


class ContentRepository:
    def __init__(self, db_client: Any):
        self.db = db_client
        self.table_name = "content_items"
        self.versions_table = "content_versions"

    async def get_by_id(self, user_id: str, content_id: str) -> Optional[Dict[str, Any]]:
        result = (
            await self.db.table(self.table_name)
            .select("*")
            .eq("id", content_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_content(
        self,
        user_id: str,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        query = (
            self.db.table(self.table_name)
            .select("*")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
        )

        if content_type:
            query = query.eq("content_type", content_type)
        if status:
            query = query.eq("status", status)

        result = await query.order("updated_at", desc=True).limit(limit).offset(offset).execute()
        return result.data or []

    async def create_content(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        content_id = str(uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        record = {
            "id": content_id,
            "user_id": user_id,
            "created_at": now_iso,
            "updated_at": now_iso,
            "latest_version_number": 1,
            "status": data.get("status", "draft"),
            **data,
        }
        result = await self.db.table(self.table_name).insert(record).execute()
        created = result.data[0] if result.data else record

        # Create initial immutable version snapshot in public.content_versions
        version_record = {
            "id": str(uuid4()),
            "user_id": user_id,
            "content_id": content_id,
            "version_number": 1,
            "body_snapshot": record["current_body"],
            "title_snapshot": record["title"],
            "change_summary": "Initial content draft creation",
            "created_by": "user",
            "created_at": now_iso,
        }
        await self.db.table(self.versions_table).insert(version_record).execute()
        return created

    async def update_content(
        self, user_id: str, content_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        change_note = updates.pop("change_note", "Manual content edit")

        # Check if body changed to trigger version increment
        existing = await self.get_by_id(user_id, content_id)
        if not existing:
            return None

        new_version_num = existing.get("latest_version_number", 1)
        if "current_body" in updates and updates["current_body"] != existing.get("current_body"):
            new_version_num += 1
            updates["latest_version_number"] = new_version_num

            # Record version snapshot
            v_record = {
                "id": str(uuid4()),
                "user_id": user_id,
                "content_id": content_id,
                "version_number": new_version_num,
                "body_snapshot": updates["current_body"],
                "title_snapshot": updates.get("title", existing["title"]),
                "change_summary": change_note,
                "created_by": "user",
                "created_at": now_iso,
            }
            await self.db.table(self.versions_table).insert(v_record).execute()

        updates["updated_at"] = now_iso
        result = (
            await self.db.table(self.table_name)
            .update(updates)
            .eq("id", content_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    async def list_versions(self, user_id: str, content_id: str) -> List[Dict[str, Any]]:
        result = (
            await self.db.table(self.versions_table)
            .select("*")
            .eq("content_id", content_id)
            .eq("user_id", user_id)
            .order("version_number", desc=True)
            .execute()
        )
        return result.data or []

    async def restore_version(
        self, user_id: str, content_id: str, version_number: int
    ) -> Optional[Dict[str, Any]]:
        """Restores an historical snapshot without deleting intervening versions."""
        versions = await self.list_versions(user_id, content_id)
        target = next((v for v in versions if v["version_number"] == version_number), None)
        if not target:
            return None

        # Update body with historical content, generating a NEW version number rather than deleting history
        return await self.update_content(
            user_id,
            content_id,
            {
                "current_body": target["body_snapshot"],
                "title": target["title_snapshot"],
                "change_note": f"Restored from version {version_number}",
            },
        )

    async def delete_content(self, user_id: str, content_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        result = (
            await self.db.table(self.table_name)
            .update({"status": "archived", "deleted_at": now_iso, "updated_at": now_iso})
            .eq("id", content_id)
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        return bool(result.data)
