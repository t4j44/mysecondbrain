"""Processing metadata for the canonical Meeting, and generic monthly usage."""
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base, FlexibleUUID
from app.models.entities import JSONEncodedDict, JSONEncodedList, Meeting, utc_now


class UsageCounter(Base):
    __tablename__ = 'usage_counters'
    __table_args__ = (UniqueConstraint('user_id', 'metric', 'period_start'),)
    user_id: Any = Column(FlexibleUUID, primary_key=True)
    metric: Any = Column(Text, primary_key=True)
    period_start: Any = Column(DateTime(timezone=True), primary_key=True)
    quantity: Any = Column(Integer, nullable=False, default=0)
    updated_at: Any = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class MeetingCapture(Base):
    __tablename__ = 'meeting_captures'
    __table_args__ = (UniqueConstraint('user_id', 'request_id'),)
    meeting_id: Any = Column(FlexibleUUID, ForeignKey('meetings.id', ondelete='CASCADE'), primary_key=True)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    request_id: Any = Column(FlexibleUUID, nullable=False)
    state: Any = Column(String(40), nullable=False, default='draft')
    audio_path: Any = Column(Text)
    audio_mime: Any = Column(Text)
    audio_checksum: Any = Column(Text)
    duration_seconds: Any = Column(Integer, nullable=False, default=0)
    charged_seconds: Any = Column(Integer, nullable=False, default=0)
    live_seconds: Any = Column(Integer, nullable=False, default=0)
    period_start: Any = Column(DateTime(timezone=True), nullable=False)
    retained_until: Any = Column(DateTime(timezone=True))
    audio_deleted_at: Any = Column(DateTime(timezone=True))
    consent_at: Any = Column(DateTime(timezone=True), nullable=False)
    data_mode: Any = Column(Text, nullable=False)
    transcript_segments: Any = Column(JSONEncodedList, nullable=False, default=list)
    intelligence: Any = Column(JSONEncodedDict, nullable=False, default=dict)
    speaker_mappings: Any = Column(JSONEncodedDict, nullable=False, default=dict)
    receipt: Any = Column(JSONEncodedDict, nullable=False, default=dict)
    confirmed_at: Any = Column(DateTime(timezone=True))
    error_code: Any = Column(String(80))
    created_at: Any = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Any = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


Meeting.capture = relationship(MeetingCapture, uselist=False, lazy='selectin', cascade='all, delete-orphan')
