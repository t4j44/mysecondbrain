"""Deterministic task answers and evidence-linked contact suggestions."""
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import String, cast, or_, select

from app.ai.indexing import owned_record, record_text, semantic_search
from app.ai.privacy import PrivacyBlocked
from app.ai.retrieval import perform_keyword_search
from app.core.errors import AIProviderError, NotFoundError
from app.models.entities import (
    Commitment,
    EntityEdge,
    Interaction,
    Person,
    PersonOrganizationRole,
    Task,
)


async def relevant_contacts(db, owner: str, query: str, limit: int = 5) -> list[dict]:
    kinds = ['person', 'interaction', 'project', 'organization', 'venture', 'meeting', 'commitment', 'document', 'memory', 'task']
    try:
        evidence = await semantic_search(db, owner, query, 20, kinds)
    except (AIProviderError, PrivacyBlocked):
        evidence = []
    literal = await perform_keyword_search(db, owner, query, 20, kinds)
    evidence = list({(item.entity_type, item.id): item for item in [*evidence, *literal]}.values())
    candidates: dict[str, list[Any]] = {}
    for item in evidence:
        identities = {item.id} if item.entity_type == 'person' else set()
        if item.entity_type in ('interaction', 'task', 'commitment', 'memory'):
            record = await owned_record(db, owner, item.entity_type, item.id)
            for field in ('person_id', 'from_person_id', 'to_person_id', 'linked_person_id'):
                if getattr(record, field, None):
                    identities.add(str(getattr(record, field)))
            identities.update(str(value) for value in getattr(record, 'related_people', []) or [])
        if item.entity_type in ('project', 'venture'):
            identities.update(str(identity) for identity in (await db.execute(select(Interaction.person_id).where(
                Interaction.user_id == owner, getattr(Interaction, item.entity_type + '_id') == item.id,
                Interaction.deleted_at.is_(None), Interaction.archived_at.is_(None),
                Interaction.person_id.is_not(None),
            ).limit(100))).scalars())
        if item.entity_type == 'meeting':
            from app.models.meetings import MeetingParticipant
            identities.update(str(identity) for identity in (await db.execute(select(MeetingParticipant.person_id).where(
                MeetingParticipant.user_id == owner, MeetingParticipant.meeting_id == item.id).limit(100))).scalars())
        if item.entity_type == 'organization':
            identities.update(str(identity) for identity in (await db.execute(select(PersonOrganizationRole.person_id).where(
                PersonOrganizationRole.user_id == owner, PersonOrganizationRole.organization_id == item.id,
                PersonOrganizationRole.deleted_at.is_(None), PersonOrganizationRole.ended_at.is_(None),
            ).limit(100))).scalars())
        edges = (await db.execute(select(EntityEdge).where(EntityEdge.user_id == owner,
            or_((EntityEdge.source_entity_type == item.entity_type) & (EntityEdge.source_entity_id == item.id),
                (EntityEdge.target_entity_type == item.entity_type) & (EntityEdge.target_entity_id == item.id)),
        ).limit(100))).scalars()
        for edge in edges:
            if (edge.metadata_payload or {}).get('interaction_id'):
                try:
                    await owned_record(db, owner, 'interaction', edge.metadata_payload['interaction_id'])
                except NotFoundError:
                    continue
            if edge.source_entity_type == 'person':
                identities.add(str(edge.source_entity_id))
            if edge.target_entity_type == 'person':
                identities.add(str(edge.target_entity_id))
        for identity in identities:
            candidates.setdefault(identity, []).append(item)
    if not candidates:
        return []
    people = (await db.execute(select(Person).where(Person.user_id == owner, Person.id.in_(candidates),
        Person.deleted_at.is_(None), Person.archived_at.is_(None)).order_by(Person.name))).scalars()
    return [{'person_id': str(person.id), 'name': person.name, 'recorded_role': person.role,
             'basis': 'Potential fit from saved records; confirm relevance and availability.',
             'evidence': [{'id': item.id, 'kind': item.entity_type, 'title': item.title,
                 'excerpt': item.snippet, 'uri': f'/sources/{item.entity_type}/{item.id}'}
                 for item in candidates[str(person.id)][:3]]}
            for person in people][:max(1, min(limit, 20))]


async def structured_answer(db, owner: str, prompt: str) -> dict | None:
    from app.ai.relationship_queries import relationship_answer
    relationship_result = await relationship_answer(db, owner, prompt)
    if relationship_result is not None:
        return relationship_result
    normalized = prompt.casefold()
    now = datetime.now(timezone.utc)
    kind = None
    model: Any
    prefix = r'(?:(?:please )?(?:show|list|get)(?: me)? )?(?:my |the )?'
    if re.fullmatch(prefix + r'overdue tasks?[.!?]?', normalized.strip()):
        kind, model, heading = 'task', Task, 'Overdue tasks (current UTC time; up to 25)'
        conditions = [Task.due_date < now, cast(Task.status, String).not_in(['done', 'completed', 'cancelled'])]
        order = Task.due_date
    elif re.fullmatch(prefix + r'(?:open|overdue) commitments?[.!?]?', normalized.strip()):
        kind, model, heading = 'commitment', Commitment, 'Open commitments (up to 25)'
        conditions = [Commitment.status == 'open']
        if 'overdue' in normalized:
            conditions.append(Commitment.due_at < now)
            heading = 'Overdue commitments (current UTC time; up to 25)'
        order = Commitment.due_at
    if kind:
        if hasattr(model, 'archived_at'):
            conditions.append(model.archived_at.is_(None))
        records = (await db.execute(select(model).where(model.user_id == owner,
            model.deleted_at.is_(None), *conditions).order_by(order).limit(25))).scalars().all()
        lines, citations = [], []
        for index, record in enumerate(records, 1):
            title = getattr(record, 'title', None) or record.description
            due = getattr(record, 'due_date', None) if kind == 'task' else record.due_at
            lines.append(f'[{index}] {title}' + (f' - due {due.isoformat()}' if due else ' - no due date'))
            citations.append({'id': str(record.id), 'entity_type': kind, 'title': title,
                'snippet': record_text(record, kind), 'uri': f'/sources/{kind}/{record.id}'})
        return {'generated_text': heading + ':\n' + ('\n'.join(lines) or 'No matching records.'),
            'provider_used': 'database', 'model_used': 'none',
            'source_citations': [item['id'] for item in citations], 'citations': citations}
    match = re.match(r'(?i)^\s*who (?:can|could|may|might) help (?:me )?(?:with|on) (.+?)[?]?$' , prompt.strip())
    if match:
        contacts = await relevant_contacts(db, owner, match.group(1)[:500])
        citations, lines = [], []
        for person in contacts:
            lines.append(f"[{len(citations) + 1}] {person['name']}: {person['basis']}")
            citations.append({'id': person['person_id'], 'entity_type': 'person', 'title': person['name'],
                'snippet': person['recorded_role'] or '', 'uri': f"/sources/person/{person['person_id']}"})
            for evidence in person['evidence']:
                lines.append(f"[{len(citations) + 1}] Recorded evidence: {evidence['excerpt'][:500]}")
                citations.append({'id': evidence['id'], 'entity_type': evidence['kind'],
                    'title': evidence['title'], 'snippet': evidence['excerpt'], 'uri': evidence['uri']})
        return {'generated_text': '\n'.join(lines) or 'No supporting relationship records found. Describe the project or skill you need.',
            'provider_used': 'database', 'model_used': 'none',
            'source_citations': [item['id'] for item in citations], 'citations': citations}
    return None
