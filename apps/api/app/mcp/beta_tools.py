"""Shared beta capabilities; authorization is enforced at both MCP transports."""
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.indexing import owned_record, semantic_search
from app.ai.privacy import PrivacyBlocked
from app.ai.retrieval import perform_keyword_search
from app.ai.structured import relevant_contacts
from app.core.errors import AIProviderError
from app.mcp.security import (
    FINALIZE_REQUIRED_SCOPES,
    READ_SCOPES,
    SCOPE_TASKS_WRITE,
)
from app.models.entities import Interaction
from app.schemas.network import CommitmentCreate, CommitmentResponse
from app.services.capture import CaptureConfirm, CaptureInput, CaptureService
from app.services.network import CommitmentService, NetworkIntelligenceService


class ContextQuery(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class BetaMCPTools:
    db: AsyncSession
    user_id: str

    async def search_context(self, query: str, limit: int = 10):
        request = ContextQuery(query=query, limit=limit)
        try:
            results = await semantic_search(self.db, self.user_id, request.query, request.limit)
        except (AIProviderError, PrivacyBlocked):
            results = []
        if not results:
            results = await perform_keyword_search(self.db, self.user_id, request.query, request.limit)
        return [item.model_dump() for item in results]

    async def find_relevant_contacts(self, query: str, limit: int = 5):
        request = ContextQuery(query=query, limit=limit)
        return await relevant_contacts(self.db, self.user_id, request.query, request.limit)

    async def search_documents(self, query: str, limit: int = 10):
        request = ContextQuery(query=query, limit=limit)
        try:
            results = await semantic_search(self.db, self.user_id, request.query, request.limit, ['document'])
        except (AIProviderError, PrivacyBlocked):
            results = []
        if not results:
            results = await perform_keyword_search(self.db, self.user_id, request.query, request.limit, ['document'])
        return [item.model_dump() for item in results]

    async def search_document_chunks(self, query: str, limit: int = 6):
        return await self.search_documents(query, max(1, min(limit, 10)))

    async def get_document_metadata(self, document_id: str):
        doc = await owned_record(self.db, self.user_id, 'document', str(UUID(document_id)))
        return {'id': str(doc.id), 'filename': doc.filename, 'checksum': doc.checksum,
                'conversion': doc.conversion_metadata or {}, 'status': doc.processing_status}

    async def get_document_section(self, document_id: str, offset: int = 0, limit: int = 3):
        from app.services.document_chunker import chunk_markdown
        record = await owned_record(self.db, self.user_id, 'document', str(UUID(document_id)))
        offset, limit = max(0, offset), max(1, min(limit, 5))
        # Canonical normalized text remains readable even when embedding is unavailable.
        chunks = chunk_markdown(record.extracted_text or '')
        rows = chunks[offset:offset + limit]
        return {'document_id': document_id, 'next_offset': offset + limit if len(chunks) > offset + limit else None,
                'sections': [{'index': row['chunk_index'], 'checksum': row['checksum'],
                    'heading': row['section_title'], 'page': row['page_number'], 'text': row['chunk_text']}
                    for row in rows]}

    async def get_person_context(self, person_id: str):
        person = await owned_record(self.db, self.user_id, 'person', str(UUID(person_id)))
        result = await NetworkIntelligenceService(self.db, self.user_id).person_relationship(person_id)
        history = (await self.db.execute(select(Interaction).where(
            Interaction.user_id == self.user_id, Interaction.person_id == person.id,
            Interaction.deleted_at.is_(None), Interaction.archived_at.is_(None),
        ).order_by(Interaction.date.desc()).limit(20))).scalars().all()
        result['where_met'] = (person.metadata_payload or {}).get('where_met')
        result['when_met'] = (person.metadata_payload or {}).get('when_met')
        result['history'] = [{'id': str(item.id), 'title': item.title, 'summary': item.summary,
            'date': item.date, 'location': item.location, 'project_id': item.project_id,
            'venture_id': item.venture_id, 'source_uri': f'/sources/interaction/{item.id}'} for item in history]
        result['source_uri'] = f'/sources/person/{person.id}'
        return jsonable_encoder(result)

    async def prepare_meeting(self, person_id: str):
        return await self.get_person_context(person_id)

    async def get_commitments(self, person_id: str | None = None, overdue_only: bool = False, limit: int = 20):
        if person_id:
            await owned_record(self.db, self.user_id, 'person', str(UUID(person_id)))
        rows = await CommitmentService(self.db, self.user_id).list_commitments(
            person_id=person_id, overdue_only=overdue_only, status='open', limit=max(1, min(limit, 100)))
        return [CommitmentResponse.model_validate(row).model_dump(mode='json') for row in rows]

    async def create_commitment(self, description: str, person_id: str | None = None, direction: str = 'unspecified', due_at: str | None = None):
        if person_id:
            await owned_record(self.db, self.user_id, 'person', str(UUID(person_id)))
        payload = CommitmentCreate.model_validate(dict(description=description, direction=direction, due_at=due_at,
            to_person_id=person_id if direction == 'owed_by_me' else None,
            from_person_id=person_id if direction != 'owed_by_me' else None, source='mcp'))
        row = await CommitmentService(self.db, self.user_id).create_commitment(payload.model_dump())
        return CommitmentResponse.model_validate(row).model_dump(mode='json')

    async def complete_commitment(self, commitment_id: str):
        row = await CommitmentService(self.db, self.user_id).complete_commitment(str(UUID(commitment_id)))
        return CommitmentResponse.model_validate(row).model_dump(mode='json')

    async def capture_context(self, text: str = '', draft_id: str | None = None, reviewed_proposal: dict | None = None, confirmed: bool = False):
        service = CaptureService(self.db, self.user_id)
        if draft_id:
            request = CaptureConfirm.model_validate({'confirmed': confirmed, 'proposal': reviewed_proposal})
            return await service.confirm(str(UUID(draft_id)), request)
        return jsonable_encoder(await service.propose(CaptureInput(text=text, source='conversation')))


def spec(name, properties, required, write=False, scopes=None):
    scopes = scopes or sorted(READ_SCOPES)
    return {'name': name, 'description': {
        'find_relevant_contacts': 'Suggest contacts only from saved context and relationship links, with evidence.',
        'search_document_chunks': 'Retrieve a bounded set of relevant document excerpts.',
        'get_document_section': 'Read a page of document sections; never returns the full document by default.',
        'get_document_metadata': 'Read conversion and source identity metadata without document body.',
        'search_documents': 'Search owned document text with semantic retrieval and a keyword fallback.',
        'search_context': 'Search approved private context with semantic retrieval and a labelled keyword fallback.',
        'get_person_context': 'Read recorded affiliations, interactions and open commitments for one person.',
        'prepare_meeting': 'Prepare a factual brief from the selected person and their recorded history.',
        'get_commitments': 'List open commitments, optionally overdue or for a person.',
        'create_commitment': 'Save an explicitly requested commitment; do not invent a promise.',
        'complete_commitment': 'Mark an explicitly identified commitment completed.',
        'capture_context': 'Propose a capture first. Show the proposal and obtain user confirmation before sending draft_id, reviewed_proposal and confirmed=true.',
    }[name], 'required_scope': scopes[0], 'additional_scopes': list(scopes[1:]), 'write': write,
        'input_schema': {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}}


STRING = {'type': 'string'}
READ_TOOLS = [
    spec('search_document_chunks', {'query': STRING, 'limit': {'type': 'integer'}}, ['query']),
    spec('get_document_metadata', {'document_id': STRING}, ['document_id']),
    spec('get_document_section', {'document_id': STRING, 'offset': {'type': 'integer'}, 'limit': {'type': 'integer'}}, ['document_id']),
    spec('find_relevant_contacts', {'query': STRING, 'limit': {'type': 'integer'}}, ['query']),
    spec('search_documents', {'query': STRING, 'limit': {'type': 'integer'}}, ['query']),
    spec('search_context', {'query': STRING, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 50}}, ['query']),
    spec('get_person_context', {'person_id': STRING}, ['person_id']),
    spec('prepare_meeting', {'person_id': STRING}, ['person_id']),
    spec('get_commitments', {'person_id': STRING, 'overdue_only': {'type': 'boolean'}, 'limit': {'type': 'integer'}}, []),
]
WRITE_TOOLS = [
    spec('create_commitment', {'description': STRING, 'person_id': STRING, 'direction': STRING, 'due_at': STRING}, ['description'], True, [SCOPE_TASKS_WRITE]),
    spec('complete_commitment', {'commitment_id': STRING}, ['commitment_id'], True, [SCOPE_TASKS_WRITE]),
    spec('capture_context', {'text': STRING, 'draft_id': STRING, 'reviewed_proposal': {'type': 'object'}, 'confirmed': {'type': 'boolean'}}, [], True, list(FINALIZE_REQUIRED_SCOPES)),
]
