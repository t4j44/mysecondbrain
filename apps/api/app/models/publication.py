"""Reviewed public snapshots, separated from private source records."""
from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.models.entities import Base, FlexibleUUID, JSONEncodedDict, generate_uuid, utc_now


class PortfolioPublication(Base):
    __tablename__ = 'portfolio_publications'
    id = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id = Column(FlexibleUUID, nullable=False, index=True)
    draft_id = Column(FlexibleUUID, ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True)
    snapshot = Column(JSONEncodedDict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class BetaFeedback(Base):
    __tablename__ = 'beta_feedback'
    id = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id = Column(FlexibleUUID, nullable=False, index=True)
    outcome = Column(String(32), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
