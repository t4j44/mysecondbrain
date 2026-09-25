"""Identity review and explicit profile updates; user knowledge takes precedence."""
import re
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.jobs.index_queue import delete_index, queue_index
from app.models.entities import JobRecord, Memory, PersonOrganizationRole, PublicProfileClaim
from app.services.person_context import correct_person_context, invalidate_drafts
from app.services.public_sources import fetch_public_page
from app.services.relationships import RelationshipService


class ResearchInput(BaseModel):
    source_url: str = Field(min_length=8, max_length=2000)


class ClaimInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    source_id: UUID
    confirmed_identity: Literal[True]
    identity_basis: str = Field(min_length=10, max_length=500)
    field: Literal['role', 'company', 'industry', 'location', 'professional_context']
    value: str = Field(min_length=1, max_length=255)
    source_quote: str = Field(min_length=10, max_length=1000)


class ClaimReview(BaseModel):
    confirmed: Literal[True]
    decision: Literal['verify', 'apply', 'reject']
    expected_current: str | None = Field(default=None, max_length=255)


def normalized(value):
    return re.sub(r'\s+', ' ', value).strip().casefold()


def claim_data(row, person):
    current = getattr(person, row.field, None) if row.field != 'professional_context' else None
    return {'id': str(row.id), 'field': row.field, 'value': row.value, 'source_url': row.source_url,
        'source_type': row.source_type, 'source_quote': row.source_quote, 'researched_at': row.researched_at,
        'identity_basis': row.identity_basis, 'confidence': row.confidence, 'confidence_reason': row.confidence_reason,
        'verification_state': row.verification_state, 'current_value': current,
        'conflict': bool(current and current != row.value)}


class EnrichmentService:
    def __init__(self, db, owner):
        self.db, self.owner = db, str(owner)
        self.relationships = RelationshipService(db, owner)

    async def research(self, person_id, payload):
        person = await self.relationships.person(person_id, lock=True)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        count = await self.db.scalar(select(func.count()).select_from(JobRecord).where(JobRecord.user_id == self.owner,
            JobRecord.job_type == 'public_profile_source', JobRecord.created_at >= cutoff))
        if count >= 10:
            raise ValidationError('The beta allows 10 public-source reviews per hour. Try again later.')
        result = await fetch_public_page(payload.source_url, person.name)
        job = JobRecord(user_id=self.owner, job_type='public_profile_source', status='completed', result_payload={
            **result, 'person_id': str(person.id), 'researched_at': datetime.now(timezone.utc).isoformat()})
        self.db.add(job)
        await self.db.commit()
        return {**job.result_payload, 'source_id': str(job.id)}

    async def propose(self, person_id, payload: ClaimInput):
        person = await self.relationships.person(person_id)
        job = (await self.db.execute(select(JobRecord).where(JobRecord.id == str(payload.source_id), JobRecord.user_id == self.owner,
            JobRecord.job_type == 'public_profile_source', JobRecord.status == 'completed'))).scalar_one_or_none()
        if not job or (job.result_payload or {}).get('person_id') != str(person.id):
            raise NotFoundError('Public source is not available for this person.')
        evidence = job.result_payload
        if normalized(payload.source_quote) not in normalized(evidence['text']) or normalized(payload.value) not in normalized(payload.source_quote):
            raise ValidationError('The claim value must appear in a verbatim quote from this reviewed source.')
        row = PublicProfileClaim(user_id=self.owner, person_id=person.id, field=payload.field, value=payload.value.strip(),
            source_url=evidence['source_url'], source_type=evidence['source_type'], source_quote=payload.source_quote,
            researched_at=datetime.fromisoformat(evidence['researched_at']), identity_basis=payload.identity_basis,
            confidence='single_source', confidence_reason='One public source; identity checked by you. Not independently corroborated.')
        self.db.add(row)
        await self.db.commit()
        return jsonable_encoder(claim_data(row, person))

    async def list(self, person_id):
        person = await self.relationships.person(person_id)
        rows = (await self.db.execute(select(PublicProfileClaim).where(PublicProfileClaim.user_id == self.owner,
            PublicProfileClaim.person_id == person.id).order_by(PublicProfileClaim.created_at.desc()).limit(100))).scalars().all()
        return [claim_data(row, person) for row in rows]

    async def claim(self, person_id, claim_id):
        person = await self.relationships.person(person_id, lock=True)
        row = (await self.db.execute(select(PublicProfileClaim).where(PublicProfileClaim.user_id == self.owner,
            PublicProfileClaim.id == str(claim_id), PublicProfileClaim.person_id == person.id).with_for_update())).scalar_one_or_none()
        if not row:
            raise NotFoundError('Public claim is not available.')
        return person, row

    async def remove_memory(self, row):
        if row.memory_id:
            memory = (await self.db.execute(select(Memory).where(Memory.id == row.memory_id, Memory.user_id == self.owner))).scalar_one_or_none()
            if memory:
                memory.deleted_at = datetime.now(timezone.utc)
                await delete_index(self.db, memory)
                await invalidate_drafts(self.db, self.owner, str(memory.id))
            row.memory_id = None
        await invalidate_drafts(self.db, self.owner, str(row.person_id))

    async def review(self, person_id, claim_id, payload: ClaimReview):
        person, row = await self.claim(person_id, claim_id)
        if payload.decision == 'reject':
            await self.remove_memory(row)
            row.verification_state = 'rejected'
        else:
            if payload.decision == 'apply':
                if row.field == 'professional_context':
                    raise ValidationError('Professional context can be saved as a reviewed source, not applied to an identity field.')
                if getattr(person, row.field) != payload.expected_current:
                    raise ConflictError('Your profile changed since review. Refresh and compare again.')
                if row.field in ('company', 'role') and person.company:
                    prior = await self.db.scalar(select(PersonOrganizationRole.id).where(PersonOrganizationRole.user_id == self.owner,
                        PersonOrganizationRole.person_id == person.id, PersonOrganizationRole.ended_at.is_(None), PersonOrganizationRole.deleted_at.is_(None)).limit(1))
                    if not prior:
                        await correct_person_context(self.db, person, {'company': person.company})
                setattr(person, row.field, row.value)
                await correct_person_context(self.db, person, {row.field: row.value})
                await invalidate_drafts(self.db, self.owner, str(person.id))
                queue_index(self.db, person)
            row.verification_state = 'verified'
            if not row.memory_id:
                memory = Memory(user_id=self.owner, title=f'Reviewed public context: {person.name}',
                    content=f'Public source claim, reviewed by the user; may be outdated. {row.field}: {row.value}.\nQuote: {row.source_quote}\nSource: {row.source_url}\nObserved: {row.researched_at.isoformat()}\nUser-recorded profile facts take precedence.',
                    source='reviewed_public_source', linked_person_id=person.id, related_people=[person.id],
                    meta={'public_claim_id': str(row.id), 'source_url': row.source_url})
                self.db.add(memory)
                await self.db.flush()
                row.memory_id = memory.id
                queue_index(self.db, memory)
        await self.db.commit()
        return claim_data(row, person)

    async def remove(self, person_id, claim_id):
        _, row = await self.claim(person_id, claim_id)
        await self.remove_memory(row)
        drafts = (await self.db.execute(select(JobRecord).where(JobRecord.user_id == self.owner, JobRecord.job_type == 'public_profile_source'))).scalars().all()
        for draft in drafts:
            data = draft.result_payload or {}
            if data.get('person_id') == str(row.person_id) and data.get('source_url') == row.source_url:
                await self.db.delete(draft)
        await self.db.delete(row)
        await self.db.commit()
        return {'removed': True, 'notice': 'Searchable public evidence removed. Profile values you explicitly approved remain editable on the profile.'}
