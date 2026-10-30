"""Bounded selection over existing V1.5 retrieval; no parallel index or record writes."""
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.indexing import SOURCES, owned_record, record_text, semantic_search
from app.ai.privacy import PrivacyBlocked
from app.ai.retrieval import perform_keyword_search
from app.ai.structured import structured_answer
from app.core.errors import AIProviderError, NotFoundError
from app.models.entities import EntityEdge


async def retrieve_prompt_context(db: AsyncSession, owner: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
    limit = max(1, min(limit, 8))
    selected: list[dict] = []
    seen: set[tuple[str, str]] = set()

    async def add(item: dict[str, Any]) -> None:
        kind, identity = item.get('entity_type') or item.get('kind'), str(item.get('id') or '')
        if not isinstance(kind, str) or kind not in SOURCES or (kind, identity) in seen or len(selected) >= limit:
            return
        try:
            row = await owned_record(db, owner, kind, identity)
        except NotFoundError:
            return
        # Existing document search supplies a relevant bounded normalized section.
        snippet = item.get('snippet') or (record_text(row, kind)[:900] if kind != 'document' else '')
        if snippet:
            selected.append({'id': identity, 'entity_type': kind, 'title': item.get('title') or getattr(row, 'name', None) or getattr(row, 'title', None) or kind,
                             'snippet': str(snippet)[:900]})
            seen.add((kind, identity))

    structured = await structured_answer(db, owner, query)
    if structured is not None:
        for item in structured.get('citations', [])[:limit]:
            await add(item)
        # A recognized temporal/structured question must not fall through to undated facts.
        return selected
    for kinds in (['venture', 'project', 'person', 'organization'], ['context_event']):
        if len(selected) < limit:
            for item in await perform_keyword_search(db, owner, query, limit, kinds):
                await add(item.model_dump())
    # Follow only current, owner-scoped edges attached to relevant saved evidence.
    for source in list(selected):
        if len(selected) >= limit:
            break
        edges = (await db.execute(select(EntityEdge).where(EntityEdge.user_id == owner,
            EntityEdge.valid_to.is_(None), or_(
                (EntityEdge.source_entity_type == source['entity_type']) & (EntityEdge.source_entity_id == source['id']),
                (EntityEdge.target_entity_type == source['entity_type']) & (EntityEdge.target_entity_id == source['id'])))
            .order_by(EntityEdge.recorded_at.desc()).limit(16))).scalars().all()
        for edge in edges:
            if edge.source_event_id:
                try:
                    await owned_record(db, owner, 'context_event', str(edge.source_event_id))
                except NotFoundError:
                    continue
            if (edge.metadata_payload or {}).get('interaction_id'):
                try:
                    await owned_record(db, owner, 'interaction', edge.metadata_payload['interaction_id'])
                except NotFoundError:
                    continue
            forward = edge.source_entity_type == source['entity_type'] and str(edge.source_entity_id) == source['id']
            kind, identity = (edge.target_entity_type, edge.target_entity_id) if forward else (edge.source_entity_type, edge.source_entity_id)
            if kind in SOURCES and kind != 'document':
                await add({'entity_type': kind, 'id': str(identity)})
    if len(selected) < limit:
        try:
            results = await semantic_search(db, owner, query, limit)
        except (AIProviderError, PrivacyBlocked):
            results = []
        for item in results:
            await add(item.model_dump())
        if len(selected) < limit:
            for item in await perform_keyword_search(db, owner, query, limit):
                await add(item.model_dump())
    return selected
