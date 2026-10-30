"""Reviewed external composer links and explicit user-reported outcomes; never sends."""
import re
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import quote, urlencode
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select

from app.core.errors import ConflictError
from app.jobs.index_queue import queue_index
from app.models.entities import AuditLog, Interaction, Memory, RelationshipAction
from app.services.context_events import create_event, event_link
from app.services.relationships import RelationshipService


class OpenOutreach(BaseModel):
    confirmed: Literal[True]
    request_id: UUID
    channel: Literal['whatsapp', 'email']
    message: str = Field(min_length=1, max_length=4000)
    subject: str = Field(default='Following up', max_length=150)

    @field_validator('message')
    @classmethod
    def nonempty_message(cls, value):
        if not value.strip():
            raise ValueError('Review a nonempty message before opening it.')
        return value


class SentOutreach(BaseModel):
    confirmed: Literal[True]
    request_id: UUID
    opened_id: UUID
    outcome: str = Field(min_length=1, max_length=2000)


def composer_url(channel, phone, email, message, subject='Following up'):
    if channel == 'whatsapp':
        number = re.sub(r'[\s().-]', '', phone or '')
        if not re.fullmatch(r'\+[1-9]\d{7,14}', number):
            raise ConflictError('Add a valid international phone number beginning with + and its country code. No country code is guessed.')
        return 'https://wa.me/' + number[1:] + '?' + urlencode({'text': message}, quote_via=quote)
    if not email or not re.fullmatch(r'[^\s@?&#\r\n]+@[^\s@?&#\r\n]+\.[^\s@?&#\r\n]+', email):
        raise ConflictError('Add a valid email address to this person before opening email.')
    if '\r' in subject or '\n' in subject:
        raise ConflictError('Email subject must be a single line.')
    return 'mailto:' + quote(email, safe='@') + '?' + urlencode({'subject': subject, 'body': message}, quote_via=quote)


async def open_outreach(db, owner, person_id, payload):
    person = await RelationshipService(db, owner).person(person_id, lock=True)
    prior = (await db.execute(select(RelationshipAction).where(RelationshipAction.user_id == owner,
        RelationshipAction.request_id == str(payload.request_id)))).scalar_one_or_none()
    if prior:
        if prior.receipt.get('deleted'):
            raise ConflictError('This outreach context was deleted. Start a new reviewed draft.')
        if str(prior.person_id) != str(person.id) or prior.action != 'opened' or prior.receipt['channel'] != payload.channel or prior.outcome != payload.message or prior.receipt['subject'] != payload.subject:
            raise ConflictError('This request identifier already belongs to a different action.')
        receipt = prior.receipt
        return {**receipt, 'url': composer_url(receipt['channel'], receipt.get('phone'), receipt.get('email'), prior.outcome, receipt['subject'])}
    url = composer_url(payload.channel, person.phone, person.email, payload.message, payload.subject)
    row = RelationshipAction(user_id=owner, person_id=person.id, request_id=str(payload.request_id),
        suggestion_key='outreach', action='opened', outcome=payload.message)
    db.add(row)
    await db.flush()
    row.receipt = {'id': str(row.id), 'channel': payload.channel, 'phone': person.phone if payload.channel == 'whatsapp' else None,
        'email': person.email if payload.channel == 'email' else None, 'subject': payload.subject, 'sent': False}
    db.add(AuditLog(user_id=owner, event_type='outreach_' + payload.channel + '_opened',
        target_entity='person', target_id=person.id, details={'outreach_id': str(row.id)}))
    await db.commit()
    return {**row.receipt, 'url': url}


async def confirm_sent(db, owner, person_id, payload):
    person = await RelationshipService(db, owner).person(person_id, lock=True)
    opened = (await db.execute(select(RelationshipAction).where(RelationshipAction.user_id == owner,
        RelationshipAction.person_id == person.id, RelationshipAction.id == str(payload.opened_id),
        RelationshipAction.action == 'opened').with_for_update())).scalar_one_or_none()
    if not opened:
        raise ConflictError('Open a reviewed draft before confirming that you sent it.')
    if opened.receipt.get('deleted'):
        raise ConflictError('This outreach context was deleted. Start a new reviewed draft.')
    key = 'outreach:' + str(opened.id)
    existing = (await db.execute(select(RelationshipAction).where(RelationshipAction.user_id == owner,
        RelationshipAction.request_id == str(payload.request_id)))).scalar_one_or_none()
    if existing and (existing.action != 'sent' or existing.suggestion_key != key):
        raise ConflictError('This request identifier already belongs to a different action.')
    prior = existing or (await db.execute(select(RelationshipAction).where(RelationshipAction.user_id == owner,
        RelationshipAction.suggestion_key == key, RelationshipAction.action == 'sent'))).scalar_one_or_none()
    if prior:
        return prior.receipt
    if not payload.outcome.strip():
        raise ConflictError('Describe the outcome you are confirming.')
    now = datetime.now(timezone.utc)
    event, _ = await create_event(db, owner, key=key, event_type='relationship_contact',
        title='Message sent (user confirmed)', summary=payload.outcome.strip(), occurred_at=now,
        source_type='user_confirmed_outreach', source_provider=opened.receipt['channel'],
        raw_text=opened.outcome, person_id=person.id,
        metadata_payload={'self_reported': True, 'opened_id': str(opened.id)})
    interaction = Interaction(user_id=owner, person_id=person.id, interaction_type='note',
        title='Message sent (user confirmed)', summary=payload.outcome.strip(), date=now,
        meta={'context_event_id': str(event.id), 'channel': opened.receipt['channel'], 'self_reported': True})
    memory = Memory(user_id=owner, title='Outreach outcome', content=payload.outcome.strip(),
        linked_person_id=person.id, related_people=[person.id], meta={'context_event_id': str(event.id)})
    db.add_all([interaction, memory])
    await db.flush()
    for kind, row in [('interaction', interaction), ('memory', memory)]:
        await event_link(db, event, kind, row.id)
        queue_index(db, row)
    person.last_interaction_at = now
    receipt = {'sent': True, 'self_reported': True, 'context_event_id': str(event.id), 'person_id': str(person.id)}
    db.add(RelationshipAction(user_id=owner, person_id=person.id, request_id=str(payload.request_id),
        suggestion_key=key, action='sent', outcome=payload.outcome, receipt=receipt))
    for name in ('outreach_confirmed_sent', 'relationship_action_completed'):
        db.add(AuditLog(user_id=owner, event_type=name, target_entity='context_event', target_id=event.id,
            details={'channel': opened.receipt['channel']}))
    await db.commit()
    return receipt
