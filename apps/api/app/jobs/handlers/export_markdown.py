import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.entities import Memory, Venture
from app.repositories.integrations import ExportRepository
from app.utils.sanitization import sanitize_filename


async def execute_export_handler(db: AsyncSession, user_id: str, payload: dict) -> dict:
    export_id = payload.get("export_id")
    export_type = payload.get("export_type", "full")

    export_repo = ExportRepository()
    record_obj = None
    if export_id:
        record_obj = await export_repo.get_by_id(
            db, user_id=user_id, id=export_id, include_archived=True
        )

    if record_obj:
        record_obj.status = "processing"
        await db.flush()

    export_dir = os.path.join(os.getcwd(), ".storage_buckets", "exports", user_id)
    os.makedirs(export_dir, exist_ok=True)

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_name = sanitize_filename(f"tajs_second_brain_export_{export_type}_{timestamp_str}.md")
    full_path = os.path.join(export_dir, archive_name)

    lines = [
        "---",
        f"export_type: {export_type}",
        f"generated_at: '{datetime.now(timezone.utc).isoformat()}'",
        "source_of_truth: 'Tajs Second Brain Canonical PostgreSQL Database'",
        "---",
        "",
        "# Taj's Second Brain — Founder Intelligence Archive",
        "",
    ]

    if export_type in {"full", "module"}:
        res_v = await db.execute(
            select(Venture).where(Venture.user_id == user_id, Venture.deleted_at.is_(None))
        )
        ventures = list(res_v.scalars().all())
        lines.append("## Strategic Ventures")
        for v in ventures:
            lines.extend(
                [
                    f"### {v.name} (Status: {v.status})",
                    f"- **Slug**: `{v.slug}` | **Priority**: {v.priority}",
                    f"- **Vision**: {v.vision or 'N/A'}",
                    "",
                ]
            )

        res_m = await db.execute(
            select(Memory).where(Memory.user_id == user_id, Memory.deleted_at.is_(None))
        )
        memories = list(res_m.scalars().all())
        lines.append("## Canonical Founder Memories")
        for m in memories:
            lines.extend(
                [
                    f"### {m.title} [{m.type.upper()}]",
                    f"- **Date**: {m.memory_date} | **Importance**: {m.importance}/10",
                    "",
                    m.body,
                    "",
                ]
            )

    with open(full_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    relative_path = f"{user_id}/{archive_name}"
    expires = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
    signed_url = f"{settings.FRONTEND_URL}/api/storage/exports/{relative_path}?token=sig_export_{timestamp_str}&expires={expires}"

    if record_obj:
        record_obj.status = "completed"
        record_obj.file_path = relative_path
        record_obj.signed_url = signed_url
        record_obj.expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
        record_obj.updated_at = datetime.now(timezone.utc)
        await db.commit()

    logger.info(f"Markdown export successfully compiled to {relative_path}.")
    return {"status": "completed", "file_path": relative_path, "signed_url": signed_url}
