from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.knowledge import (
    DocumentRepository,
    MemoryEmbeddingRepository,
    MemoryRepository,
)
from app.schemas.knowledge import SearchResultItem


async def perform_keyword_search(
    db: AsyncSession, user_id: str, query: str, limit: int = 10
) -> List[SearchResultItem]:
    """
    Keyword / substring search across stored embedding content rows.

    This is NOT semantic or vector retrieval. Confidence scores are unavailable
    until real cosine ranking is implemented (G4).
    """
    emb_repo = MemoryEmbeddingRepository()
    embeddings = await emb_repo.search_by_keyword(
        db, user_id=user_id, query_text=query, limit=limit
    )

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
                score=None,
                confidence_available=False,
                search_mode="keyword",
            )
        )
    return results


# Backward-compatible alias — name must not imply hybrid/vector ranking.
async def perform_hybrid_search(
    db: AsyncSession, user_id: str, query: str, limit: int = 10
) -> List[SearchResultItem]:
    return await perform_keyword_search(db, user_id, query, limit)


def format_rag_context(items: List[SearchResultItem]) -> str:
    if not items:
        return "No corresponding context discovered in Taj's Second Brain."
    lines = [
        "Here is keyword-matched contextual evidence from Taj's Second Brain "
        "(not semantic vector ranking):\n"
    ]
    for idx, item in enumerate(items, 1):
        score_note = (
            f", score={item.score}"
            if item.score is not None
            else ", confidence=unavailable"
        )
        lines.append(
            f"[{idx}] Source (ID: {item.id}, Type: {item.entity_type}, "
            f"Title: {item.title}{score_note}):"
        )
        lines.append(f"    {item.snippet}\n")
    return "\n".join(lines)
