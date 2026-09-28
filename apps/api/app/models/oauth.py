from typing import Any

from sqlalchemy import Column, DateTime, Text

from app.models.base import Base, FlexibleUUID
from app.models.entities import JSONEncodedDict, JSONEncodedList, utc_now
from app.utils.identifiers import generate_uuid


class OAuthClient(Base):
    __tablename__ = 'mcp_oauth_clients'
    id: Any = Column(Text, primary_key=True)
    metadata_payload: Any = Column('metadata', JSONEncodedDict, nullable=False)
    secret_hash: Any = Column(Text)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class OAuthRequest(Base):
    __tablename__ = 'mcp_oauth_requests'
    request_hash: Any = Column(Text, primary_key=True)
    user_id: Any = Column(FlexibleUUID)
    client_id: Any = Column(Text, nullable=False)
    payload: Any = Column(JSONEncodedDict, nullable=False)
    expires_at: Any = Column(DateTime(timezone=True), nullable=False)
    consumed_at: Any = Column(DateTime(timezone=True))


class OAuthGrant(Base):
    __tablename__ = 'mcp_oauth_grants'
    id: Any = Column(FlexibleUUID, primary_key=True, default=generate_uuid)
    user_id: Any = Column(FlexibleUUID, nullable=False)
    client_id: Any = Column(Text, nullable=False)
    client_name: Any = Column(Text, nullable=False)
    scopes: Any = Column(JSONEncodedList, nullable=False)
    issuer: Any = Column(Text, nullable=False)
    resource: Any = Column(Text, nullable=False)
    created_at: Any = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at: Any = Column(DateTime(timezone=True), nullable=False)
    last_used_at: Any = Column(DateTime(timezone=True))
    revoked_at: Any = Column(DateTime(timezone=True))


class OAuthCode(Base):
    __tablename__ = 'mcp_oauth_codes'
    code_hash: Any = Column(Text, primary_key=True)
    user_id: Any = Column(FlexibleUUID, nullable=False)
    grant_id: Any = Column(FlexibleUUID, nullable=False)
    code_challenge: Any = Column(Text, nullable=False)
    redirect_uri: Any = Column(Text, nullable=False)
    expires_at: Any = Column(DateTime(timezone=True), nullable=False)
    consumed_at: Any = Column(DateTime(timezone=True))


class OAuthTokenRecord(Base):
    __tablename__ = 'mcp_oauth_tokens'
    token_hash: Any = Column(Text, primary_key=True)
    user_id: Any = Column(FlexibleUUID, nullable=False)
    grant_id: Any = Column(FlexibleUUID, nullable=False)
    kind: Any = Column(Text, nullable=False)
    scopes: Any = Column(JSONEncodedList, nullable=False)
    expires_at: Any = Column(DateTime(timezone=True), nullable=False)
    consumed_at: Any = Column(DateTime(timezone=True))
