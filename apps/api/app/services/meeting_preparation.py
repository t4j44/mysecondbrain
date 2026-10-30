"""Small, deterministic preparation cards from explicit canonical participant links."""
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import lazyload

from app.core.errors import NotFoundError
from app.models.entities import ACTIVE_COMMITMENT_STATUSES, Commitment, Interaction, Meeting, Person
from app.models.meetings import MeetingParticipant
from app.services.relationships import active, source


def excerpt(value, maximum=300):
    value = (value or '').strip()
    return value if len(value) <= maximum else value[:maximum].rstrip() + '…'


def evidence(record, kind):
    reference = source(record, kind)
    return {**reference, 'title': excerpt(reference['title'], 120)}


async def prepare(db, owner, identity):
    meeting = await db.scalar(select(Meeting).options(lazyload('*')).where(
        *active(Meeting, owner), Meeting.id == identity))
    if not meeting:
        raise NotFoundError('Meeting is not available.')
    now = datetime.now(timezone.utc)
    participant_ids = select(MeetingParticipant.person_id).where(MeetingParticipant.user_id == owner,
        MeetingParticipant.meeting_id == meeting.id)
    people = (await db.scalars(select(Person).where(*active(Person, owner), Person.id.in_(participant_ids))
        .order_by(Person.name, Person.id).limit(6))).all()
    cards = []
    for person in people[:5]:
        latest = await db.scalar(select(Interaction).where(*active(Interaction, owner),
            Interaction.person_id == person.id, Interaction.date <= now)
            .order_by(Interaction.date.desc(), Interaction.id).limit(1))
        promises = (await db.scalars(select(Commitment).where(*active(Commitment, owner),
            Commitment.status.in_(ACTIVE_COMMITMENT_STATUSES),
            or_(Commitment.from_person_id == person.id, Commitment.to_person_id == person.id))
            .order_by(Commitment.due_at.asc().nullslast(), Commitment.created_at.desc(), Commitment.id).limit(4))).all()
        cards.append({'person': evidence(person, 'person'),
            'saved_role': excerpt(person.role, 100), 'saved_company': excerpt(person.company, 100),
            'notes': excerpt(person.notes),
            'last_interaction': {'source': evidence(latest, 'interaction'),
                'summary': excerpt(latest.summary or latest.title), 'date': latest.date} if latest else None,
            'commitments': [{'source': evidence(row, 'commitment'), 'description': excerpt(row.description),
                'direction': row.direction, 'status': row.status, 'due_at': row.due_at,
                'revision': row.revision} for row in promises[:3]], 'more_commitments': len(promises) > 3})
    return {'meeting': evidence(meeting, 'meeting'), 'generated_at': now, 'people': cards,
        'more_people': len(people) > 5, 'basis': 'Saved records only. Calendar freshness is not verified.'}
