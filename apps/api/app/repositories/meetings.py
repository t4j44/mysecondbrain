from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, asc, delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.errors import NotFoundError
from app.jobs.index_queue import delete_index, queue_index
from app.models.entities import Person
from app.models.meetings import Meeting, MeetingParticipant
from app.schemas.meetings import MeetingCreate, MeetingUpdate


class MeetingsRepository:
    @staticmethod
    async def create_meeting(db: AsyncSession, user_id: UUID, schema: MeetingCreate) -> Meeting:
        db_meeting = Meeting(
            user_id=user_id,
            venture_id=schema.venture_id,
            title=schema.title,
            meeting_date=schema.meeting_date,
            duration_minutes=schema.duration_minutes,
            location=schema.location,
            recording_url=schema.recording_url,
            transcript_text=schema.transcript_text,
            ai_summary=schema.ai_summary,
            action_items=schema.action_items,
            meta=schema.metadata,
        )
        db.add(db_meeting)
        await db.flush()  # Extract ID

        # Link participants
        for person_id in schema.participant_person_ids:
            # Check owner of person
            p_query = select(Person).where(and_(Person.id == person_id, Person.user_id == user_id))
            p_result = await db.execute(p_query)
            if not p_result.scalar_one_or_none():
                raise NotFoundError(f"Participant with ID {person_id} not found in workspace.")

            db_part = MeetingParticipant(
                user_id=user_id,
                meeting_id=db_meeting.id,
                person_id=person_id,
                attendance_status="attended",
            )
            db.add(db_part)

        await db.flush()
        if db_meeting.deleted_at or db_meeting.archived_at:
            await delete_index(db, db_meeting)
        else:
            queue_index(db, db_meeting)
        await db.commit()
        await db.refresh(db_meeting)
        return db_meeting

    @staticmethod
    async def get_meeting(db: AsyncSession, user_id: UUID, meeting_id: UUID) -> Meeting:
        query = select(Meeting).where(
            and_(
                Meeting.id == meeting_id,
                Meeting.user_id == user_id,
                Meeting.deleted_at.is_(None),
            )
        )
        result = await db.execute(query)
        db_meeting = result.scalar_one_or_none()
        if not db_meeting:
            raise NotFoundError("Meeting not found or access denied.")
        # `participants` is an eager relationship over public.meeting_participants.
        return db_meeting

    @staticmethod
    async def list_meetings(
        db: AsyncSession,
        user_id: UUID,
        venture_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "meeting_date",
        sort_order: str = "desc",
    ) -> Tuple[List[Meeting], int]:
        query = select(Meeting).where(
            and_(Meeting.user_id == user_id, Meeting.deleted_at.is_(None))
        )

        if venture_id:
            query = query.where(Meeting.venture_id == venture_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Sorting
        sort_attr = getattr(Meeting, sort_by, Meeting.meeting_date)
        if sort_order == "desc":
            query = query.order_by(desc(sort_attr))
        else:
            query = query.order_by(asc(sort_attr))

        # Pagination
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all()), total

    @staticmethod
    async def update_meeting(
        db: AsyncSession, user_id: UUID, meeting_id: UUID, schema: MeetingUpdate
    ) -> Meeting:
        db_meeting = await MeetingsRepository.get_meeting(db, user_id, meeting_id)

        update_data = schema.dict(exclude_unset=True)
        participant_ids = update_data.pop("participant_person_ids", None)
        if "metadata" in update_data:
            update_data["meta"] = update_data.pop("metadata")

        for key, value in update_data.items():
            setattr(db_meeting, key, value)

        db_meeting.updated_at = datetime.utcnow()

        if participant_ids is not None:
            # Drop old participants
            del_query = delete(MeetingParticipant).where(
                and_(
                    MeetingParticipant.meeting_id == meeting_id,
                    MeetingParticipant.user_id == user_id,
                )
            )
            await db.execute(del_query)

            # Insert new participants
            for person_id in participant_ids:
                p_query = select(Person).where(
                    and_(Person.id == person_id, Person.user_id == user_id)
                )
                p_result = await db.execute(p_query)
                if not p_result.scalar_one_or_none():
                    raise NotFoundError(f"Participant with ID {person_id} not found in workspace.")

                db_part = MeetingParticipant(
                    user_id=user_id,
                    meeting_id=meeting_id,
                    person_id=person_id,
                    attendance_status="attended",
                )
                db.add(db_part)

        await db.flush()
        if db_meeting.deleted_at or db_meeting.archived_at:
            await delete_index(db, db_meeting)
        else:
            queue_index(db, db_meeting)
        await db.commit()
        await db.refresh(db_meeting)
        return db_meeting

    @staticmethod
    async def soft_delete_meeting(db: AsyncSession, user_id: UUID, meeting_id: UUID) -> Meeting:
        db_meeting = await MeetingsRepository.get_meeting(db, user_id, meeting_id)
        db_meeting.deleted_at = datetime.utcnow()
        await db.flush()
        if db_meeting.deleted_at or db_meeting.archived_at:
            await delete_index(db, db_meeting)
        else:
            queue_index(db, db_meeting)
        await db.commit()
        await db.refresh(db_meeting)
        return db_meeting
