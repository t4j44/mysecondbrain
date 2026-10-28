"""Owner preferences and a server-only messaging connection vault."""
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.models.base import Base, FlexibleUUID
from app.models.entities import JSONEncodedDict, utc_now
from app.utils.identifiers import generate_uuid


class AssistantPreferences(Base):
    __tablename__ = 'assistant_preferences'
    user_id: Any = Column(FlexibleUUID, primary_key=True)
    timezone: Any = Column(Text, nullable=False)
    quiet_start_minute: Any = Column(Integer, nullable=False, default=1320)
    quiet_end_minute: Any = Column(Integer, nullable=False, default=480)
    quiet_enabled: Any = Column(Boolean, nullable=False, default=True)
    telegram_enabled: Any = Column(Boolean, nullable=False, default=False)
    include_details: Any = Column(Boolean, nullable=False, default=False)
    daily_cap: Any = Column(Integer, nullable=False, default=3)
    version: Any = Column(Integer, nullable=False, default=1)
    consent_at: Any = Column(DateTime(timezone=True))
    revoked_at: Any = Column(DateTime(timezone=True))
    updated_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class MessagingConnection(Base):
    __tablename__ = 'messaging_connections'
    __table_args__ = (UniqueConstraint('user_id', 'provider'),
        UniqueConstraint('user_id', 'id'),
        UniqueConstraint('provider', 'external_chat_hash'), UniqueConstraint('provider', 'external_user_hash'))
    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    provider: Any = Column(String(30), nullable=False, default='telegram')
    status: Any = Column(String(20), nullable=False, default='pending')
    external_chat_hash: Any = Column(Text)
    external_user_hash: Any = Column(Text)
    encrypted_chat_id: Any = Column(Text)
    encrypted_user_id: Any = Column(Text)
    nonce_hash: Any = Column(Text, unique=True)
    nonce_expires_at: Any = Column(DateTime(timezone=True))
    revision: Any = Column(Integer, nullable=False, default=1)
    linked_at: Any = Column(DateTime(timezone=True))
    revoked_at: Any = Column(DateTime(timezone=True))
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class MessagingUpdateReceipt(Base):
    __tablename__ = 'messaging_update_receipts'
    __table_args__ = (ForeignKeyConstraint(['user_id', 'connection_id'],
        ['messaging_connections.user_id', 'messaging_connections.id'], ondelete='CASCADE'),)
    provider: Any = Column(String(30), primary_key=True, default='telegram')
    update_id: Any = Column(BigInteger, primary_key=True)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    connection_id: Any = Column(FlexibleUUID, nullable=False)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class CommitmentAction(Base):
    __tablename__ = 'commitment_actions'
    __table_args__ = (UniqueConstraint('user_id', 'request_id'),
        ForeignKeyConstraint(['user_id', 'commitment_id'],
            ['commitments.user_id', 'commitments.id'], ondelete='CASCADE'))
    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False, index=True)
    commitment_id: Any = Column(FlexibleUUID, nullable=False)
    request_id: Any = Column(FlexibleUUID, nullable=False)
    action: Any = Column(String(20), nullable=False)
    request_hash: Any = Column(String(64), nullable=False)
    receipt: Any = Column(JSONEncodedDict, nullable=False)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
