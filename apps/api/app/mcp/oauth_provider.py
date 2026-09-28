"""Durable OAuth provider for the official MCP SDK. No provider token passthrough."""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    RegistrationError,
    TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from sqlalchemy import func, select

from app.core.config import settings
from app.dependencies.database import admin_db_session
from app.mcp.security import FINALIZE_REQUIRED_SCOPES, READ_SCOPES, SCOPE_CONTENT_DRAFT
from app.models.entities import AccountClosure, AuditLog
from app.models.oauth import OAuthClient, OAuthCode, OAuthGrant, OAuthRequest, OAuthTokenRecord

SCOPES = sorted(READ_SCOPES | set(FINALIZE_REQUIRED_SCOPES) | {SCOPE_CONTENT_DRAFT, 'mcp:projects:write', 'offline_access'})
DEFAULT_SCOPES = sorted(READ_SCOPES)
ACCESS_SECONDS = 900
REFRESH_DAYS = 30


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def now():
    return datetime.now(timezone.utc)


def issuer():
    return settings.MCP_ISSUER_URL.rstrip('/')


def resource():
    return settings.MCP_RESOURCE_SERVER_URL


def valid_redirect(value):
    url = urlparse(value)
    local = url.scheme == 'http' and url.hostname in {'127.0.0.1', 'localhost', '::1'}
    return bool((url.scheme == 'https' or local) and url.hostname and not url.fragment
                and not url.username and not url.password and '*' not in value and len(value) <= 2048)


class DatabaseOAuthProvider:
    async def exchange_identity_assertion(self, client, params):
        raise TokenError('unsupported_grant_type', 'Identity assertion grants are not supported.')

    async def get_client(self, client_id):
        async with admin_db_session(reason='oauth_client_metadata') as db:
            row = await db.get(OAuthClient, client_id)
            if not row:
                return None
            # secret_hash intentionally isn't passed as a secret to SDK handlers.
            # The application authenticator verifies the presented secret against its hash.
            return OAuthClientInformationFull.model_validate(row.metadata_payload)

    async def register_client(self, client_info):
        redirects = client_info.redirect_uris or []
        if not redirects or len(redirects) > 10 or not all(valid_redirect(str(url)) for url in redirects):
            raise RegistrationError('invalid_redirect_uri', 'Use exact HTTPS callback URLs, or explicit loopback callbacks for development.')
        if client_info.token_endpoint_auth_method not in {'none', 'client_secret_post', 'client_secret_basic'}:
            raise RegistrationError('invalid_client_metadata', 'Unsupported token authentication method.')
        if set(client_info.grant_types) - {'authorization_code', 'refresh_token'} or client_info.response_types != ['code']:
            raise RegistrationError('invalid_client_metadata', 'Only authorization code with optional refresh is supported.')
        if len(client_info.client_name or '') > 120:
            raise RegistrationError('invalid_client_metadata', 'Client name is too long.')
        values = client_info.model_dump(mode='json', exclude={'client_secret'})
        async with admin_db_session(reason='oauth_client_registration') as db:
            full = (await db.scalar(select(func.count()).select_from(OAuthClient))) >= 5000
            if not full:
                db.add(OAuthClient(id=client_info.client_id, metadata_payload=values,
                    secret_hash=digest(client_info.client_secret) if client_info.client_secret else None))
                await db.commit()
        if full:
            raise RegistrationError('invalid_client_metadata', 'Beta client registration limit reached.')

    async def authorize(self, client, params: AuthorizationParams):
        scopes = params.scopes or DEFAULT_SCOPES
        if params.resource != resource():
            raise AuthorizeError('invalid_target', 'The resource must match this MCP endpoint.')
        if set(scopes) - set(SCOPES):
            raise AuthorizeError('invalid_scope', 'Only declared granular scopes may be requested.')
        if not params.redirect_uri_provided_explicitly or str(params.redirect_uri) not in [str(url) for url in client.redirect_uris or []]:
            raise AuthorizeError('invalid_request', 'An exact registered redirect URI is required.')
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', params.code_challenge):
            raise AuthorizeError('invalid_request', 'PKCE S256 is required.')
        token = secrets.token_urlsafe(32)
        values = params.model_dump(mode='json') | {'scopes': scopes}
        async with admin_db_session(reason='oauth_authorization_request') as db:
            db.add(OAuthRequest(request_hash=digest(token), client_id=client.client_id,
                payload=values, expires_at=now() + timedelta(minutes=10)))
            await db.commit()
        return settings.FRONTEND_URL.rstrip('/') + '/oauth/consent#request=' + token

    async def active_grant(self, db, identity):
        grant = await db.get(OAuthGrant, identity)
        if not grant or grant.revoked_at or utc(grant.expires_at) <= now() or grant.issuer != issuer() or grant.resource != resource():
            return None
        if await db.get(AccountClosure, grant.user_id):
            return None
        return grant

    async def load_authorization_code(self, client, authorization_code):
        async with admin_db_session(reason='oauth_code_lookup') as db:
            row = await db.get(OAuthCode, digest(authorization_code))
            grant = await self.active_grant(db, row.grant_id) if row else None
            if not row or not grant or grant.client_id != client.client_id or row.consumed_at:
                return None
            return AuthorizationCode(code=authorization_code, scopes=grant.scopes,
                expires_at=utc(row.expires_at).timestamp(), client_id=grant.client_id,
                code_challenge=row.code_challenge, redirect_uri=row.redirect_uri,
                redirect_uri_provided_explicitly=True, resource=grant.resource, subject=str(grant.user_id))

    async def issue_tokens(self, db, grant, scopes, refresh_allowed=True):
        access = 'sb_oauth_' + secrets.token_urlsafe(32)
        db.add(OAuthTokenRecord(token_hash=digest(access), user_id=grant.user_id, grant_id=grant.id,
            kind='access', scopes=[s for s in scopes if s != 'offline_access'], expires_at=now() + timedelta(seconds=ACCESS_SECONDS)))
        refresh = None
        if refresh_allowed and 'offline_access' in scopes:
            refresh = 'sb_refresh_' + secrets.token_urlsafe(32)
            db.add(OAuthTokenRecord(token_hash=digest(refresh), user_id=grant.user_id, grant_id=grant.id,
                kind='refresh', scopes=scopes, expires_at=grant.expires_at))
        return OAuthToken(access_token=access, token_type='Bearer', expires_in=ACCESS_SECONDS,  # nosec B106 - OAuth scheme
                          refresh_token=refresh, scope=' '.join(scopes))

    async def exchange_authorization_code(self, client, authorization_code):
        token = None
        async with admin_db_session(reason='oauth_code_exchange') as db:
            row = (await db.execute(select(OAuthCode).where(OAuthCode.code_hash == digest(authorization_code.code))
                .with_for_update())).scalar_one_or_none()
            grant = await self.active_grant(db, row.grant_id) if row else None
            if row and grant and not row.consumed_at and utc(row.expires_at) > now() and grant.client_id == client.client_id:
                row.consumed_at = now()
                token = await self.issue_tokens(db, grant, grant.scopes, 'refresh_token' in client.grant_types)
                await db.commit()
        # SDK errors are frozen dataclasses; raise after the async context manager,
        # which otherwise tries to assign __traceback__ and hides the OAuth error.
        if token is None:
            raise TokenError('invalid_grant', 'Authorization code is unavailable.')
        return token

    async def load_refresh_token(self, client, refresh_token):
        async with admin_db_session(reason='oauth_refresh_lookup') as db:
            row = await db.get(OAuthTokenRecord, digest(refresh_token))
            grant = await self.active_grant(db, row.grant_id) if row else None
            if not row or row.kind != 'refresh' or not grant or grant.client_id != client.client_id:
                return None
            # Used refresh tokens reach exchange so replay invalidates the whole family.
            return RefreshToken(token=refresh_token, client_id=grant.client_id, scopes=row.scopes,
                expires_at=int(utc(row.expires_at).timestamp()), subject=str(grant.user_id))

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        failure = None
        token = None
        async with admin_db_session(reason='oauth_refresh_rotation') as db:
            row = (await db.execute(select(OAuthTokenRecord).where(OAuthTokenRecord.token_hash == digest(refresh_token.token))
                .with_for_update())).scalar_one_or_none()
            grant = await self.active_grant(db, row.grant_id) if row else None
            if not row or row.kind != 'refresh' or not grant or grant.client_id != client.client_id or utc(row.expires_at) <= now():
                failure = TokenError('invalid_grant', 'Refresh token is unavailable.')
            elif row.consumed_at:
                grant.revoked_at = now()
                db.add(AuditLog(user_id=grant.user_id, event_type='mcp_oauth_revoked', target_entity='oauth_grant',
                    target_id=grant.id, details={'reason': 'refresh_reuse'}))
                await db.commit()
                failure = TokenError('invalid_grant', 'Refresh token reuse revoked this connection.')
            elif set(scopes) - set(row.scopes):
                failure = TokenError('invalid_scope', 'Scopes cannot be increased during refresh.')
            else:
                row.consumed_at = now()
                token = await self.issue_tokens(db, grant, scopes)
                await db.commit()
        if failure:
            raise failure
        return token

    async def load_access_token(self, token):
        if not token.startswith('sb_oauth_'):
            return None
        async with admin_db_session(reason='oauth_access_verification') as db:
            row = await db.get(OAuthTokenRecord, digest(token))
            grant = await self.active_grant(db, row.grant_id) if row else None
            if not row or row.kind != 'access' or not grant or utc(row.expires_at) <= now():
                return None
            grant.last_used_at = now()
            await db.commit()
            return AccessToken(token=token, client_id=grant.client_id, scopes=row.scopes,
                expires_at=int(utc(row.expires_at).timestamp()), resource=grant.resource,
                subject=str(grant.user_id), claims={'iss': grant.issuer, 'grant_id': str(grant.id), 'client_name': grant.client_name})

    async def revoke_token(self, token):
        async with admin_db_session(reason='oauth_token_revocation') as db:
            row = await db.get(OAuthTokenRecord, digest(token.token))
            if row:
                grant = await db.get(OAuthGrant, row.grant_id)
                if grant and not grant.revoked_at:
                    grant.revoked_at = now()
                    db.add(AuditLog(user_id=grant.user_id, event_type='mcp_oauth_revoked',
                        target_entity='oauth_grant', target_id=grant.id, details={}))
                    await db.commit()


oauth_provider = DatabaseOAuthProvider()
