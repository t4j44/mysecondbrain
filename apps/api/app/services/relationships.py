"""Shared, evidence-based relationship capabilities. No autonomous external actions."""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, model_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import lazyload

from app.ai.indexing import SOURCES, owned_record
from app.ai.message_draft import (
    MAX_FACT_CHARS,
    MAX_STYLE_EXAMPLES,
    DraftFacts,
    clip,
    first_name_of,
    write_draft,
)
from app.ai.provider import get_llm_provider
from app.core.errors import ConflictError, NotFoundError
from app.jobs.index_queue import queue_index
from app.models.crm import Relationship
from app.models.entities import (
    ACTIVE_COMMITMENT_STATUSES,
    AuditLog,
    Commitment,
    ContextEvent,
    EmailContact,
    EntityEdge,
    Interaction,
    Meeting,
    Memory,
    Person,
    PersonOrganizationRole,
    Project,
    RelationshipAction,
    Task,
)
from app.models.meetings import MeetingParticipant


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def active(model, owner):
    clauses = [model.user_id == owner, model.deleted_at.is_(None)]
    if hasattr(model, 'archived_at'):
        clauses.append(model.archived_at.is_(None))
    return clauses


def source(record, kind):
    return {'id': str(record.id), 'kind': kind,
        'title': getattr(record, 'name', None) or getattr(record, 'title', None)
                 or getattr(record, 'description', None) or 'Saved record',
        'uri': f'/people/{record.id}' if kind == 'person' else f'/sources/{kind}/{record.id}'}


def recency(last, count, now=None):
    now = now or datetime.now(timezone.utc)
    days = max(0, (now - utc(last)).days) if last else None
    label = 'Unknown' if days is None else ('Active' if days <= 14 else 'Warm' if days <= 45 else 'Cooling' if days <= 90 else 'Dormant')
    return {'label': label, 'days_since': days, 'interaction_count': count,
        'explanation': f'{count} recorded interactions. ' + (f'Last recorded contact {days} days ago.' if days is not None else 'No dated contact recorded.'),
        'rule': 'Recency only: Active ≤14 days; Warm 15–45; Cooling 46–90; Dormant >90. This does not measure personal closeness.'}


class FollowupActionInput(BaseModel):
    confirmed: Literal[True]
    request_id: UUID
    suggestion_key: str = Field(min_length=1, max_length=200)
    action: Literal['completed', 'scheduled', 'dismissed']
    outcome: str | None = Field(default=None, max_length=2000)
    scheduled_at: AwareDatetime | None = None

    @model_validator(mode='after')
    def validate_action(self):
        if self.action == 'completed' and not (self.outcome or '').strip():
            raise ValueError('Describe what actually happened before recording completion.')
        if self.action == 'scheduled' and (not self.scheduled_at or self.scheduled_at <= datetime.now(timezone.utc)):
            raise ValueError('Choose a future reminder date.')
        return self


class RelationshipService:
    def __init__(self, db, owner):
        self.db, self.owner = db, str(owner)

    async def rows(self, model, *clauses, limit=100, order=None):
        # These previews use scalar columns and explicitly owner-scoped queries.
        # Do not implicitly preload entire participant/capture relationships.
        statement = select(model).options(lazyload('*')).where(*active(model, self.owner), *clauses)
        if order is not None:
            statement = statement.order_by(order)
        return (await self.db.execute(statement.limit(limit))).scalars().all()

    async def person(self, identity, lock=False):
        statement = select(Person).where(*active(Person, self.owner), Person.id == str(identity))
        if lock:
            statement = statement.with_for_update()
        person = (await self.db.execute(statement)).scalar_one_or_none()
        if not person:
            raise NotFoundError('Person is not available.')
        return person

    async def email_dates(self, identities):
        """Latest date mail went to, and came from, each person across connected Google accounts. Dates only."""
        rows = (await self.db.execute(select(EmailContact).where(EmailContact.user_id == self.owner,
            EmailContact.person_id.in_([str(item) for item in identities])))).scalars().all()
        found = {}
        for row in rows:
            slot = found.setdefault(str(row.person_id), {'sent': None, 'received': None})
            for key, value in (('sent', utc(row.last_sent_at)), ('received', utc(row.last_received_at))):
                if value and (slot[key] is None or value > slot[key]):
                    slot[key] = value
        return found

    async def profile(self, identity):
        person = await self.person(identity)
        identity = str(person.id)
        history = await self.rows(Interaction, Interaction.person_id == identity, order=Interaction.date.desc())
        commitments = await self.rows(Commitment, or_(Commitment.from_person_id == identity, Commitment.to_person_id == identity), order=Commitment.due_at.asc())
        tasks = await self.rows(Task, Task.person_id == identity, order=Task.due_date.asc())
        stats = (await self.db.execute(select(func.count(), func.min(Interaction.date), func.max(Interaction.date)).where(*active(Interaction, self.owner), Interaction.person_id == identity))).one()
        related = {}

        async def add(kind, record_id, reason, evidence):
            if kind not in SOURCES or not record_id or (kind == 'person' and str(record_id) == identity):
                return
            if (kind, str(record_id)) in related:
                return
            try:
                record = await owned_record(self.db, self.owner, kind, str(record_id))
            except NotFoundError:
                return
            related.setdefault((kind, str(record_id)), {**source(record, kind), 'reason': reason, 'evidence': evidence})

        for item in history:
            for kind in ('project', 'venture', 'meeting'):
                await add(kind, getattr(item, kind + '_id', None), 'Linked to a recorded interaction.', source(item, 'interaction'))
        edges = (await self.db.execute(select(EntityEdge).where(EntityEdge.user_id == self.owner, EntityEdge.valid_to.is_(None),
            or_((EntityEdge.source_entity_type == 'person') & (EntityEdge.source_entity_id == identity),
                (EntityEdge.target_entity_type == 'person') & (EntityEdge.target_entity_id == identity))).order_by(EntityEdge.created_at.desc()).limit(150))).scalars().all()
        for edge in edges:
            if edge.source_event_id:
                try:
                    await owned_record(self.db, self.owner, 'context_event', str(edge.source_event_id))
                except NotFoundError:
                    continue
            kind, record_id = (edge.target_entity_type, edge.target_entity_id) if edge.source_entity_type == 'person' and str(edge.source_entity_id) == identity else (edge.source_entity_type, edge.source_entity_id)
            # Ignore obsolete capture-derived edges after source interaction deletion.
            evidence = source(person, 'person')
            if (edge.metadata_payload or {}).get('interaction_id'):
                try:
                    origin = await owned_record(self.db, self.owner, 'interaction', edge.metadata_payload['interaction_id'])
                    evidence = source(origin, 'interaction')
                except NotFoundError:
                    continue
            await add(kind, record_id, (edge.metadata_payload or {}).get('reason') or 'Explicit saved connection: ' + edge.relationship_type.replace('_', ' '), evidence)
        roles = (await self.db.execute(select(PersonOrganizationRole).where(PersonOrganizationRole.user_id == self.owner,
            PersonOrganizationRole.person_id == identity, PersonOrganizationRole.deleted_at.is_(None)).order_by(PersonOrganizationRole.created_at.desc()).limit(50))).scalars().all()
        affiliations = []
        for role in roles:
            try:
                org = await owned_record(self.db, self.owner, 'organization', str(role.organization_id))
            except NotFoundError:
                continue
            affiliations.append({**source(org, 'organization'), 'role': role.role, 'current': not role.ended_at, 'started_at': role.started_at, 'ended_at': role.ended_at})
            await add('organization', org.id, 'Recorded affiliation.', source(org, 'organization'))
        await add('organization', person.organization_id, 'Current organization recorded on this profile.', source(person, 'person'))
        links = (await self.db.execute(select(Relationship).where(Relationship.user_id == self.owner,
            or_(Relationship.source_person_id == identity, Relationship.target_person_id == identity)).limit(50))).scalars().all()
        for link in links:
            other = link.target_person_id if str(link.source_person_id) == identity else link.source_person_id
            await add('person', other, link.relationship_nature, source(person, 'person'))
        meetings = (await self.db.execute(select(MeetingParticipant.meeting_id).where(MeetingParticipant.user_id == self.owner,
            MeetingParticipant.person_id == identity).limit(50))).scalars().all()
        for meeting_id in meetings:
            await add('meeting', meeting_id, 'Recorded meeting participant.', source(person, 'person'))
        emailed = (await self.email_dates([identity])).get(identity, {'sent': None, 'received': None})
        last = max((utc(value) for value in (stats[2], person.last_interaction_at, *emailed.values()) if value), default=None)
        profile = {'person': {**source(person, 'person'), 'name': person.name, 'role': person.role, 'company': person.company,
            'industry': person.industry, 'location': person.location, 'email': person.email, 'phone': person.phone,
            'linkedin_url': person.linkedin_url, 'notes': person.notes, 'where_met': (person.metadata_payload or {}).get('where_met'),
            'when_met': (person.metadata_payload or {}).get('when_met'), 'relationship_type': person.relationship_type},
            'first_interaction': stats[1], 'last_interaction': last, 'recency': recency(last, stats[0]),
            'email_contact': {'last_sent_at': emailed['sent'], 'last_received_at': emailed['received']},
            'timeline': [{**source(row, 'interaction'), 'date': row.date, 'summary': row.summary, 'location': row.location,
                'topics': (row.meta or {}).get('topics', [])} for row in history],
            'topics': sorted({topic for row in history for topic in (row.meta or {}).get('topics', []) if isinstance(topic, str)}),
            'affiliations': affiliations, 'related': list(related.values()),
            'commitments': [{**source(row, 'commitment'), 'direction': row.direction, 'status': row.status, 'due_at': row.due_at} for row in commitments],
            'tasks': [{**source(row, 'task'), 'status': row.status, 'due_at': row.due_date} for row in tasks],
            'brief': [{ 'text': f'{person.name}' + (f' — {person.role}' if person.role else '') + (f' at {person.company}' if person.company else ''), 'evidence': source(person, 'person')}],
            'limits': 'Latest 100 interactions, commitments and tasks; up to 150 explicit links. Brief is computed from saved facts.'}
        if history:
            profile['brief'].append({'text': 'Last discussion: ' + (history[0].summary or history[0].title), 'evidence': source(history[0], 'interaction')})
        profile['followups'] = await self.followups(identity)
        from app.services.context_events import event_list
        profile['moments'] = await event_list(self.db, self.owner, person_id=identity)
        return profile

    async def connect(self, person_id, kind, record_id, reason):
        person = await self.person(person_id, lock=True)
        record = await owned_record(self.db, self.owner, kind, str(record_id))
        if kind == 'person' and str(record.id) == str(person.id):
            raise ConflictError('Choose a different person to connect.')
        edge = (await self.db.execute(select(EntityEdge).where(EntityEdge.user_id == self.owner, EntityEdge.valid_to.is_(None),
            EntityEdge.source_entity_type == 'person', EntityEdge.source_entity_id == person.id,
            EntityEdge.target_entity_type == kind, EntityEdge.target_entity_id == record.id,
            EntityEdge.relationship_type == 'user_confirmed'))).scalar_one_or_none()
        if edge is None:
            edge = EntityEdge(user_id=self.owner, source_entity_type='person', source_entity_id=person.id,
                target_entity_type=kind, target_entity_id=record.id, relationship_type='user_confirmed')
            self.db.add(edge)
        edge.metadata_payload = {'reason': reason.strip(), 'confirmed': True}
        await self.db.commit()
        return {**source(record, kind), 'reason': reason}

    async def people_for_record(self, kind, record_id):
        await owned_record(self.db, self.owner, kind, str(record_id))
        edges = (await self.db.execute(select(EntityEdge).where(EntityEdge.user_id == self.owner, EntityEdge.valid_to.is_(None),
            EntityEdge.source_entity_type == 'person', EntityEdge.target_entity_type == kind,
            EntityEdge.target_entity_id == str(record_id)).limit(100))).scalars().all()
        result, seen = [], set()
        for edge in edges:
            if edge.source_event_id:
                try:
                    await owned_record(self.db, self.owner, 'context_event', str(edge.source_event_id))
                except NotFoundError:
                    continue
            if str(edge.source_entity_id) in seen:
                continue
            if (edge.metadata_payload or {}).get('interaction_id'):
                try:
                    await owned_record(self.db, self.owner, 'interaction', edge.metadata_payload['interaction_id'])
                except NotFoundError:
                    continue
            try:
                person = await self.person(edge.source_entity_id)
            except NotFoundError:
                continue
            seen.add(str(person.id))
            result.append({**source(person, 'person'), 'reason': (edge.metadata_payload or {}).get('reason') or 'Linked through confirmed relationship context.'})
        return result

    async def home(self):
        followups = await self.followups()
        recent = await self.rows(Interaction, Interaction.person_id.is_not(None), limit=12, order=Interaction.date.desc())
        people_ids = {str(row.person_id) for row in recent}
        people = await self.rows(Person, Person.id.in_(people_ids), limit=100)
        names = {str(p.id): p.name for p in people}
        projects = await self.rows(Project, Project.status.in_(['active', 'planned']), limit=6, order=Project.updated_at.desc())
        connections = await self._home_project_connections(projects)
        work = [{**source(project, 'project'), 'people': connections[str(project.id)][:5]} for project in projects]
        meetings = await self.rows(Meeting, Meeting.start_time >= datetime.now(timezone.utc), Meeting.status != 'cancelled', limit=6, order=Meeting.start_time.asc())
        participants: dict[str, list[dict]] = {str(meeting.id): [] for meeting in meetings}
        if meetings:
            ranked_participants = select(MeetingParticipant.id, func.row_number().over(
                partition_by=MeetingParticipant.meeting_id, order_by=(Person.name, Person.id)).label('position'))\
                .join(Person, Person.id == MeetingParticipant.person_id).where(
                    MeetingParticipant.user_id == self.owner, *active(Person, self.owner),
                    MeetingParticipant.meeting_id.in_([meeting.id for meeting in meetings])).subquery()
            rows = (await self.db.execute(select(MeetingParticipant.meeting_id, Person)
                .join(ranked_participants, ranked_participants.c.id == MeetingParticipant.id)
                .join(Person, Person.id == MeetingParticipant.person_id).where(ranked_participants.c.position <= 20)
                .order_by(Person.name, Person.id))).all()
            for meeting_id, person in rows:
                if len(participants[str(meeting_id)]) < 20:
                    participants[str(meeting_id)].append(source(person, 'person'))
        upcoming = [{**source(meeting, 'meeting'), 'date': meeting.start_time, 'people': participants[str(meeting.id)]} for meeting in meetings]
        return {'followups': followups, 'meetings': upcoming, 'projects': work,
            'recent_activity': [{**source(row, 'interaction'), 'date': row.date, 'summary': row.summary,
                'person_id': str(row.person_id), 'name': names[str(row.person_id)]} for row in recent if str(row.person_id) in names],
            'opportunities': [{'person_id': str(row.person_id), 'name': names[str(row.person_id)], 'reason': row.summary or row.title,
                'evidence': source(row, 'interaction'), 'basis': 'Recorded offer or opportunity; verify whether it is still available.'}
                for row in recent if str(row.person_id) in names and any(word in (row.summary or '').casefold() for word in ('introduc', 'offered', 'opportunity'))],
            'limits': 'Up to 50 follow-ups from 500 contacts, 6 active projects and meetings, 12 recent interactions.'}

    async def _home_project_connections(self, projects):
        """Batch the home preview without weakening deleted-source/owner checks.

        Window limits apply per project, so one busy project cannot crowd out
        the other five. Query count does not grow with contacts or projects.
        """
        result: dict[str, list[dict]] = {str(project.id): [] for project in projects}
        if not projects:
            return result
        identities = [project.id for project in projects]
        by_id = {str(project.id): project for project in projects}
        seen: dict[str, set[str]] = {str(project.id): set() for project in projects}
        ranked = select(Interaction.id, func.row_number().over(partition_by=Interaction.project_id,
            order_by=(Interaction.date.desc(), Interaction.id)).label('position')).where(
                *active(Interaction, self.owner), Interaction.project_id.in_(identities), Interaction.person_id.is_not(None)).subquery()
        rows = (await self.db.execute(select(Interaction, Person).options(lazyload('*')).join(ranked, ranked.c.id == Interaction.id)
            .join(Person, Person.id == Interaction.person_id).where(ranked.c.position <= 30, *active(Person, self.owner))
            .order_by(Interaction.date.desc(), Interaction.id))).all()
        for interaction, person in rows:
            project_id, person_id = str(interaction.project_id), str(person.id)
            if person_id not in seen[project_id]:
                seen[project_id].add(person_id)
                result[project_id].append({'person_id': person_id, 'name': person.name,
                    'reason': interaction.summary or interaction.title, 'evidence': source(interaction, 'interaction')})
        ranked_edges = select(EntityEdge.id, func.row_number().over(partition_by=EntityEdge.target_entity_id,
            order_by=(EntityEdge.created_at.desc(), EntityEdge.id)).label('position')).where(
                EntityEdge.user_id == self.owner, EntityEdge.valid_to.is_(None),
                EntityEdge.source_entity_type == 'person', EntityEdge.target_entity_type == 'project',
                EntityEdge.target_entity_id.in_(identities)).subquery()
        edges = (await self.db.execute(select(EntityEdge, Person).join(ranked_edges, ranked_edges.c.id == EntityEdge.id)
            .join(Person, Person.id == EntityEdge.source_entity_id).where(ranked_edges.c.position <= 100,
                *active(Person, self.owner)).order_by(EntityEdge.created_at.desc(), EntityEdge.id))).all()
        event_ids = {edge.source_event_id for edge, _ in edges if edge.source_event_id}
        evidence_ids = {(edge.metadata_payload or {}).get('interaction_id') for edge, _ in edges} - {None}
        events = set((await self.db.execute(select(ContextEvent.id).where(*active(ContextEvent, self.owner),
            ContextEvent.id.in_(event_ids)))).scalars().all()) if event_ids else set()
        evidence = {str(value) for value in (await self.db.execute(select(Interaction.id).where(*active(Interaction, self.owner),
            Interaction.id.in_(evidence_ids)))).scalars().all()} if evidence_ids else set()
        for edge, person in edges:
            if edge.source_event_id and edge.source_event_id not in events:
                continue
            interaction_id = (edge.metadata_payload or {}).get('interaction_id')
            if interaction_id and str(interaction_id) not in evidence:
                continue
            project_id, person_id = str(edge.target_entity_id), str(person.id)
            if person_id not in seen[project_id]:
                seen[project_id].add(person_id)
                result[project_id].append({'person_id': person_id, 'name': person.name,
                    'reason': (edge.metadata_payload or {}).get('reason') or 'Linked through confirmed relationship context.',
                    'evidence': source(by_id[project_id], 'project')})
        return result

    async def followups(self, person_id=None, limit=50):
        people = await self.rows(Person, *([Person.id == str(person_id)] if person_id else []), limit=500, order=Person.name.asc())
        if not people:
            return []
        identities = [str(p.id) for p in people]
        latest = (await self.db.execute(select(Interaction.person_id, func.max(Interaction.date), func.count()).where(*active(Interaction, self.owner), Interaction.person_id.in_(identities)).group_by(Interaction.person_id))).all()
        dates = {str(row[0]): (row[1], row[2]) for row in latest}
        emailed = await self.email_dates(identities)
        obligations = await self.rows(Commitment, Commitment.status.in_(ACTIVE_COMMITMENT_STATUSES), or_(Commitment.from_person_id.in_(identities), Commitment.to_person_id.in_(identities)), limit=1000, order=Commitment.due_at.asc())
        actions = (await self.db.execute(select(RelationshipAction).where(RelationshipAction.user_id == self.owner,
            RelationshipAction.person_id.in_(identities)).order_by(RelationshipAction.created_at.desc()).limit(2000))).scalars().all()
        receipts = {}
        for action in actions:
            receipts.setdefault(action.suggestion_key, action)
        now = datetime.now(timezone.utc)
        result = []
        for person in people:
            identity = str(person.id)
            recorded, count = dates.get(identity, (None, 0))
            mail = emailed.get(identity, {})
            last = max((utc(value) for value in (recorded, person.last_interaction_at, *mail.values()) if value), default=None)
            strength = recency(last, count, now)
            candidates = []
            for item in obligations:
                if identity not in (str(item.from_person_id), str(item.to_person_id)):
                    continue
                if item.due_at and utc(item.due_at) > now + timedelta(days=7):
                    continue
                key = f'commitment:{item.id}:{utc(item.updated_at).isoformat()}'
                reason = ('You promised: ' if item.direction == 'owed_by_me' else 'Open promise: ') + item.description
                reason += f' Due {utc(item.due_at).date()}.' if item.due_at else ' No due date recorded.'
                candidates.append((key, reason, source(item, 'commitment'), item.due_at, str(item.id)))
            due = utc(person.follow_up_date)
            if (due and due <= now) or (not due and strength['days_since'] is not None and strength['days_since'] > 45):
                key = 'contact:' + identity + ':' + hashlib.sha256(f'{last}|{due}'.encode()).hexdigest()[:20]
                reason = f'Follow-up was set for {due.date()}.' if due and due <= now else strength['explanation']
                candidates.append((key, reason, source(person, 'person'), due, None))
            for key, reason, evidence, due_at, commitment_id in candidates:
                receipt = receipts.get(key)
                if receipt and (receipt.action != 'scheduled' or utc(receipt.scheduled_at) > now):
                    continue
                result.append({'key': key, 'person_id': identity, 'name': person.name, 'why_now': reason,
                    'context': ' · '.join(str(x) for x in (person.role, person.company, (person.metadata_payload or {}).get('where_met')) if x),
                    'suggested_action': 'Review the promise and record what happened.' if commitment_id else 'Check in and record the outcome.',
                    'evidence': evidence, 'due_at': due_at, 'commitment_id': commitment_id, 'recency': strength})
        result.sort(key=lambda item: (utc(item['due_at']) or now, item['name'], item['key']))
        return result[:max(1, min(limit, 100))]

    async def _draft_facts(self, person, why_now=None, commitment=None):
        """Only the owner's own saved records; the drafter may state nothing beyond these lines."""
        identity = str(person.id)
        detail = ', '.join(str(x) for x in (person.role, person.company) if x)
        lines = [clip(f'Recipient: {person.name}' + (f' ({detail})' if detail else ''), MAX_FACT_CHARS)]
        where = (person.metadata_payload or {}).get('where_met')
        if where:
            lines.append(clip(f'You met at: {where}', MAX_FACT_CHARS))
        if why_now:
            lines.append(clip(f'Why you are writing now: {why_now}', MAX_FACT_CHARS))
        if commitment is not None:
            lines.append(clip(('You promised: ' if commitment.direction == 'owed_by_me' else 'They promised you: ')
                              + commitment.description, MAX_FACT_CHARS))
        recent = await self.rows(Interaction, Interaction.person_id == identity, limit=3, order=Interaction.date.desc())
        for item in recent:
            when = utc(item.date).date().isoformat() if item.date else 'undated'
            lines.append(clip(f'Past contact ({when}): ' + ' '.join(x for x in (item.title, item.summary) if x), MAX_FACT_CHARS))
        mail = (await self.email_dates([identity])).get(identity, {})
        for label, value in (('You last emailed them on', mail.get('sent')), ('They last emailed you on', mail.get('received'))):
            if value:
                lines.append(f'{label} {value.date().isoformat()}.')
        last = max((utc(item.date) for item in recent if item.date), default=None)
        days = (datetime.now(timezone.utc) - last).days if last else None
        if days is not None:
            lines.append(f'You last spoke {days} days ago.')
        return DraftFacts(first_name=first_name_of(person.name), lines=lines,
            commitment=commitment.description if commitment is not None else None,
            commitment_owed_by_me=commitment is not None and commitment.direction == 'owed_by_me',
            long_silence=days is not None and days > 45)

    async def _style_examples(self, person_id):
        """The user's own recently reviewed messages, newest first, this person's before others'."""
        rows = (await self.db.execute(select(RelationshipAction).where(RelationshipAction.user_id == self.owner,
            RelationshipAction.action == 'opened').order_by(RelationshipAction.created_at.desc()).limit(30))).scalars().all()
        mine, others, seen = [], [], set()
        for row in rows:
            text = (row.outcome or '').strip()
            if not text or (row.receipt or {}).get('deleted') or text in seen:
                continue
            seen.add(text)
            (mine if str(row.person_id) == str(person_id) else others).append(text)
        return (mine + others)[:MAX_STYLE_EXAMPLES]

    async def _compose(self, person, why_now=None, commitment=None):
        facts = await self._draft_facts(person, why_now, commitment)
        result = await write_draft(get_llm_provider('gemini'), facts, await self._style_examples(person.id))
        self.db.add(AuditLog(user_id=self.owner, event_type='outreach_draft_created', target_entity='person',
            target_id=person.id, details={'source': result.source}))
        await self.db.commit()
        notice = ('Written from your saved context. Editable draft only. Nothing has been sent.' if result.source == 'ai' else
            'Simple draft because AI drafting was unavailable. Add your own update. Nothing has been sent.')
        return {'draft': result.text, 'source': result.source, 'needs_edit': result.needs_edit, 'notice': notice}

    async def draft(self, person_id, key):
        person = await self.person(person_id)
        suggestion = next((item for item in await self.followups(person_id, 100) if item['key'] == key), None)
        if not suggestion:
            raise ConflictError('This suggestion changed. Refresh the relationship context.')
        commitment = await owned_record(self.db, self.owner, 'commitment', suggestion['commitment_id']) if suggestion['commitment_id'] else None
        return {**await self._compose(person, suggestion['why_now'], commitment), 'evidence': suggestion['evidence']}

    async def person_draft(self, person_id):
        return await self._compose(await self.person(person_id))

    async def act(self, person_id, payload: FollowupActionInput):
        person = await self.person(person_id, lock=True)
        existing = (await self.db.execute(select(RelationshipAction).where(RelationshipAction.user_id == self.owner,
            RelationshipAction.request_id == str(payload.request_id)))).scalar_one_or_none()
        if existing:
            if str(existing.person_id) != str(person.id) or existing.suggestion_key != payload.suggestion_key or existing.action != payload.action:
                raise ConflictError('This request identifier already belongs to a different action.')
            return existing.receipt
        suggestion = next((item for item in await self.followups(person_id, 100) if item['key'] == payload.suggestion_key), None)
        if not suggestion:
            raise ConflictError('This suggestion changed or was already handled. Refresh before acting.')
        now = datetime.now(timezone.utc)
        receipt: dict[str, Any] = {'action': payload.action, 'person_id': str(person.id), 'records': []}
        if payload.action == 'completed':
            from app.services.context_events import create_event, event_link
            event, _ = await create_event(self.db, self.owner, key='followup:' + str(payload.request_id),
                event_type='relationship_contact', title='Follow-up outcome', summary=(payload.outcome or '').strip(),
                raw_text=(payload.outcome or '').strip(), occurred_at=now, source_type='user_confirmed_outcome',
                person_id=person.id, metadata_payload={'self_reported': True})
            receipt['context_event_id'] = str(event.id)
            interaction = Interaction(user_id=self.owner, person_id=person.id, interaction_type='note',
                title='Follow-up outcome', summary=(payload.outcome or '').strip(), date=now,
                meta={'relationship_action_request': str(payload.request_id)})
            memory = Memory(user_id=self.owner, title=f'Follow-up with {person.name}', content=(payload.outcome or '').strip(),
                linked_person_id=person.id, related_people=[person.id], meta={'relationship_action_request': str(payload.request_id)})
            self.db.add_all([interaction, memory])
            await self.db.flush()
            for kind, record in [('interaction', interaction), ('memory', memory)]:
                await event_link(self.db, event, kind, record.id)
                queue_index(self.db, record)
                receipt['records'].append(source(record, kind))
                self.db.add(EntityEdge(user_id=self.owner, source_entity_type='person', source_entity_id=person.id,
                    target_entity_type=kind, target_entity_id=record.id, relationship_type='followup_outcome'))
            if suggestion['commitment_id']:
                commitment = await owned_record(self.db, self.owner, 'commitment', suggestion['commitment_id'])
                commitment.status, commitment.completed_at = 'completed', now
                queue_index(self.db, commitment)
                from app.services.commitment_actions import complete_linked_tasks
                await complete_linked_tasks(self.db, self.owner, commitment.id, now)
            person.last_interaction_at = now
            if person.follow_up_date and utc(person.follow_up_date) <= now:
                person.follow_up_date = None
            prior = (await self.db.execute(select(RelationshipAction).where(RelationshipAction.user_id == self.owner,
                RelationshipAction.person_id == person.id, RelationshipAction.suggestion_key == payload.suggestion_key,
                RelationshipAction.action == 'scheduled'))).scalars().all()
            for action in prior:
                for item in (action.receipt or {}).get('records', []):
                    if item.get('kind') == 'task':
                        try:
                            task = await owned_record(self.db, self.owner, 'task', item['id'])
                        except NotFoundError:
                            continue
                        task.status, task.completion_date = 'done', now
                        queue_index(self.db, task)
        elif payload.action == 'scheduled':
            task = Task(user_id=self.owner, person_id=person.id, title=f'Follow up with {person.name}',
                description=suggestion['why_now'], due_date=payload.scheduled_at)
            self.db.add(task)
            await self.db.flush()
            queue_index(self.db, task)
            receipt['records'].append(source(task, 'task'))
        self.db.add(RelationshipAction(user_id=self.owner, person_id=person.id, request_id=str(payload.request_id),
            suggestion_key=payload.suggestion_key, action=payload.action, outcome=payload.outcome,
            scheduled_at=payload.scheduled_at, receipt=receipt))
        self.db.add(AuditLog(user_id=self.owner, event_type='relationship_action_' + payload.action,
            target_entity='person', target_id=person.id, details={'request_id': str(payload.request_id)}))
        await self.db.commit()
        return receipt
