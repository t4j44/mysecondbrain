from sqlalchemy import delete

from app.models.entities import JobRecord, MemoryEmbedding
from app.models.rag import Embedding

KINDS = {"memories": "memory", "people": "person", "organizations": "organization",
         "interactions": "interaction", "meetings": "meeting", "projects": "project",
         "tasks": "task", "commitments": "commitment", "ventures": "venture",
         "achievements": "achievement", "work_sessions": "work_session",
         "evidence_items": "evidence", "decisions": "decision"}


def queue_index(db, record):
    kind = KINDS.get(record.__tablename__)
    if kind:
        db.add(JobRecord(user_id=record.user_id, job_type="index_record", status="pending",
                        result_payload={"kind": kind, "record_id": str(record.id)}))


async def delete_index(db, record):
    kind = KINDS.get(record.__tablename__, "document" if record.__tablename__ == "documents" else None)
    if kind:
        await db.execute(delete(Embedding).where(Embedding.user_id == record.user_id,
            Embedding.source_record_type == kind, Embedding.source_record_id == record.id))
        await db.execute(delete(MemoryEmbedding).where(MemoryEmbedding.user_id == record.user_id,
            MemoryEmbedding.entity_type == kind, MemoryEmbedding.entity_id == record.id))
