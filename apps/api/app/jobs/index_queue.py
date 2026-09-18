from sqlalchemy import delete, or_, text

from app.models.entities import EntityEdge, JobRecord, MemoryEmbedding
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
        if db.bind.dialect.name == 'postgresql':
            await db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))'),
                {'key': f'index:{record.user_id}:{kind}:{record.id}'})
        await db.execute(delete(EntityEdge).where(EntityEdge.user_id == record.user_id, or_(
            (EntityEdge.source_entity_type == kind) & (EntityEdge.source_entity_id == record.id),
            (EntityEdge.target_entity_type == kind) & (EntityEdge.target_entity_id == record.id))))
        await db.execute(delete(Embedding).where(Embedding.user_id == record.user_id,
            Embedding.source_record_type == kind, Embedding.source_record_id == record.id))
        await db.execute(delete(MemoryEmbedding).where(MemoryEmbedding.user_id == record.user_id,
            MemoryEmbedding.entity_type == kind, MemoryEmbedding.entity_id == record.id))
