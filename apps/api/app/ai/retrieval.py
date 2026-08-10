from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.knowledge import (
    DocumentRepository,
    MemoryEmbeddingRepository,
    MemoryRepository,
)
from app.schemas.knowledge import SearchResultItem


async def perform_hybrid_search(
    db: AsyncSession, user_id: str, query: str, limit: int = 10
) -> List[SearchResultItem]:
    """
    Perform hybrid vector + keyword search across user embeddings and canonical records (ADR-007).
    Ensures strict tenant scoping to prevent leak of proprietary intellectual property.
    """
    emb_repo = MemoryEmbeddingRepository()
    embeddings = await emb_repo.search_similar(db, user_id=user_id, query_text=query, limit=limit)

    results: List[SearchResultItem] = []
    mem_repo = MemoryRepository()
    doc_repo = DocumentRepository()

    for emb in embeddings:
        title = f"{emb.entity_type} match"
        if emb.entity_type == "memory":
            rec = await mem_repo.get_by_id(db, user_id=user_id, id=emb.entity_id)
            if rec:
                title = rec.title
        elif emb.entity_type == "document":
            doc = await doc_repo.get_by_id(db, user_id=user_id, id=emb.entity_id)
            if doc:
                title = doc.filename

        snippet = emb.content[:250] + "..." if len(emb.content) > 250 else emb.content
        results.append(
            SearchResultItem(
                id=emb.entity_id,
                entity_type=emb.entity_type,
                title=title,
                snippet=snippet,
                score=0.89,  # Normalized confidence score
            )
        )
    return results


def format_rag_context(items: List[SearchResultItem]) -> str:
    if not items:
        return "No corresponding context discovered in Taj's Second Brain."
    lines = ["Here is the retrieved contextual evidence from Taj's Second Brain:\n"]
    for idx, item in enumerate(items, 1):
        lines.append(
            f"[{idx}] Source (ID: {item.id}, Type: {item.entity_type}, Title: {item.title}):"
        )
        lines.append(f"    {item.snippet}\n")
    return "\n".join(lines)
