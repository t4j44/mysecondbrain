"""Meeting compatibility model and participant junction."""

from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.models.base import Base, FlexibleUUID
from app.models.entities import Meeting, utc_now
from app.utils.identifiers import generate_uuid


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    meeting_id: Any = Column(
        FlexibleUUID, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Any = Column(
        FlexibleUUID, ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    attendance_status: Any = Column(String(50), nullable=False, default="attended")
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


__all__ = ["Meeting", "MeetingParticipant"]
