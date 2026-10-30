"""Select bounded excerpts, never whole-document context for ordinary answers."""
from sqlalchemy import select

from app.core.config import settings
from app.models.rag import DocumentChunk


async def bounded_context(db, owner, items, prompt):
    budget = max(0, min(settings.RAG_CONTEXT_MAX_CHARS, settings.AI_MAX_INPUT_CHARS - len(prompt) - 500))
    window = max(0, min(settings.RAG_NEIGHBOR_WINDOW, 2))
    selected, parts, seen = [], [], set()
    for item in items:
        key = (item.entity_type, item.chunk_id or item.id)
        if key in seen:
            continue
        excerpt = item.snippet
        if item.entity_type == 'document' and item.chunk_id and item.chunk_index is not None and window:
            neighbors = (await db.execute(select(DocumentChunk).where(
                DocumentChunk.user_id == owner, DocumentChunk.document_id == item.id,
                DocumentChunk.chunk_index.between(item.chunk_index - window, item.chunk_index + window),
            ).order_by(DocumentChunk.chunk_index))).scalars().all()
            expanded = '\n\n'.join(row.chunk_text for row in neighbors)
            if expanded and len(expanded) < budget // 2:
                excerpt = expanded
        part = f'[{len(selected) + 1}] {excerpt}'
        if len(part) + 2 > budget:
            continue  # Preserve complete retrieved sections; do not cut mid-sentence.
        seen.add(key)
        selected.append(item)
        parts.append(part)
        budget -= len(part) + 2
    return selected, '\n\n'.join(parts)
