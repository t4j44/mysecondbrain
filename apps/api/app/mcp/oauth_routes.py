"""OAuth HTTP adapters: official SDK handlers plus durable consent and strict binding."""
import base64
import binascii
import hmac
import re
import secrets
from datetime import timedelta
from typing import Literal
from urllib.parse import unquote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from mcp.server.auth.handlers.authorize import AuthorizationHandler
from mcp.server.auth.handlers.register import RegistrationHandler
from mcp.server.auth.handlers.token import TokenHandler
from mcp.server.auth.middleware.client_auth import AuthenticationError, ClientAuthenticator
from mcp.server.auth.provider import construct_redirect_uri
from mcp.server.auth.settings import ClientRegistrationOptions
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.datastructures import FormData
from starlette.responses import JSONResponse, Response

from app.dependencies.auth import AuthenticatedUser, get_current_user
from app.dependencies.database import admin_db_session, get_rls_db_session
from app.mcp.oauth_provider import (
    DEFAULT_SCOPES,
    REFRESH_DAYS,
    SCOPES,
    digest,
    issuer,
    now,
    oauth_provider,
    resource,
    utc,
)
from app.models.entities import AuditLog
from app.models.oauth import OAuthClient, OAuthCode, OAuthGrant, OAuthRequest

router = APIRouter(tags=['MCP OAuth'])
PRIVATE = {'Cache-Control': 'no-store', 'Pragma': 'no-cache'}


def error(code='invalid_request', description='Invalid OAuth request.', status=400):
    return JSONResponse({'error': code, 'error_description': description}, status_code=status, headers=PRIVATE)


class HashedClientAuthenticator(ClientAuthenticator):
    async def authenticate_request(self, request):
        form = await request.form()
        client_id = str(form.get('client_id') or '')
        header = request.headers.get('authorization', '')
        supplied = str(form.get('client_secret') or '')
        used = 'client_secret_post' if supplied else 'none'
        if header:
            if not header.startswith('Basic ') or supplied:
                raise AuthenticationError('Use one registered client authentication method.')
            try:
                decoded = base64.b64decode(header[6:], validate=True).decode()
                basic_id, supplied = (unquote(part) for part in decoded.split(':', 1))
                if client_id and basic_id != client_id:
                    raise ValueError('mismatch')
                if not client_id:
                    client_id = basic_id
                    # SDK 2.0 expects client_id in its token request model even
                    # when RFC 6749 Basic authentication carries it in the header.
                    request._form = FormData([*form.multi_items(), ('client_id', client_id)])
            except (ValueError, binascii.Error, UnicodeError) as exc:
                raise AuthenticationError('Invalid client authentication.') from exc
            used = 'client_secret_basic'
        client = await oauth_provider.get_client(client_id)
        if not client or client.token_endpoint_auth_method != used:
            raise AuthenticationError('Invalid client authentication.')
        if used != 'none':
            async with admin_db_session(reason='oauth_client_authentication') as db:
                row = await db.get(OAuthClient, client_id)
                if not row or not row.secret_hash or not hmac.compare_digest(row.secret_hash, digest(supplied)):
                    raise AuthenticationError('Invalid client authentication.')
        return client


authenticator = HashedClientAuthenticator(oauth_provider)


@router.get('/.well-known/oauth-authorization-server')
async def authorization_metadata():
    origin = issuer()
    return {'issuer': origin, 'authorization_endpoint': origin + '/oauth/authorize',
        'token_endpoint': origin + '/oauth/token', 'registration_endpoint': origin + '/oauth/register',
        'revocation_endpoint': origin + '/oauth/revoke', 'response_types_supported': ['code'],
        'grant_types_supported': ['authorization_code', 'refresh_token'],
        'token_endpoint_auth_methods_supported': ['none', 'client_secret_post', 'client_secret_basic'],
        'code_challenge_methods_supported': ['S256'], 'scopes_supported': SCOPES,
        'authorization_response_iss_parameter_supported': True,
        'client_id_metadata_document_supported': False}


@router.get('/.well-known/oauth-protected-resource')
@router.get('/.well-known/oauth-protected-resource/mcp')
async def protected_resource_metadata():
    return {'resource': resource(), 'authorization_servers': [issuer()],
        'scopes_supported': [scope for scope in SCOPES if scope != 'offline_access'], 'bearer_methods_supported': ['header'],
        'resource_name': 'Second Brain private context'}


@router.post('/oauth/register')
async def register(request: Request):
    if len(await request.body()) > 16000:
        return error('invalid_client_metadata', 'Client metadata exceeds the size limit.')
    options = ClientRegistrationOptions(enabled=True, valid_scopes=SCOPES, default_scopes=DEFAULT_SCOPES)
    return await RegistrationHandler(oauth_provider, options).handle(request)


@router.get('/oauth/authorize')
async def authorize(request: Request):
    params = request.query_params
    if len(str(params)) > 12000 or len(params) != len(params.multi_items()):
        return error()
    if params.get('code_challenge_method') != 'S256' or not params.get('redirect_uri'):
        return error(description='An explicit registered callback and PKCE S256 are required.')
    return await AuthorizationHandler(oauth_provider).handle(request)


@router.post('/oauth/token')
async def token(request: Request):
    if len(await request.body()) > 16000:
        return error()
    form = await request.form()
    if len(form) != len(form.multi_items()):
        return error()
    # SDK 2.0 validates PKCE/redirect/code expiry, but does not enforce the token
    # request's resource indicator. Enforce it here before the SDK can exchange.
    if form.get('resource') != resource():
        return error('invalid_target', 'resource must match the protected MCP endpoint.')
    if form.get('grant_type') == 'authorization_code':
        if not re.fullmatch(r'[A-Za-z0-9._~-]{43,128}', str(form.get('code_verifier') or '')):
            return error('invalid_grant', 'Invalid PKCE verifier.')
        if form.get('scope'):
            client = await oauth_provider.get_client(str(form.get('client_id') or ''))
            code = await oauth_provider.load_authorization_code(client, str(form.get('code') or '')) if client else None
            if not code or set(str(form['scope']).split()) != set(code.scopes):
                return error('invalid_scope', 'Authorization code scopes cannot be changed.')
    return await TokenHandler(oauth_provider, authenticator).handle(request)


@router.post('/oauth/revoke')
async def revoke(request: Request):
    if len(await request.body()) > 16000:
        return error()
    try:
        client = await authenticator.authenticate_request(request)
    except AuthenticationError:
        return error('invalid_client', 'Invalid client authentication.', 401)
    form = await request.form()
    value = str(form.get('token') or '')
    if not value or len(form) != len(form.multi_items()):
        return error()
    loaded = await oauth_provider.load_access_token(value) or await oauth_provider.load_refresh_token(client, value)
    if loaded and loaded.client_id == client.client_id:
        await oauth_provider.revoke_token(loaded)
    return Response(status_code=200, headers=PRIVATE)


class ConsentRequest(BaseModel):
    request: str = Field(min_length=40, max_length=100)


class ConsentDecision(ConsentRequest):
    confirmed: Literal[True]
    approve: bool
    scopes: list[str] = Field(default_factory=list, max_length=20)


async def pending_request(db, secret, owner):
    row = (await db.execute(select(OAuthRequest).where(OAuthRequest.request_hash == digest(secret))
        .with_for_update())).scalar_one_or_none()
    if not row or row.consumed_at or utc(row.expires_at) <= now() or (row.user_id and str(row.user_id) != owner):
        raise HTTPException(400, 'This authorization request is unavailable. Start again from your AI client.')
    row.user_id = owner
    return row


@router.post('/oauth/consent/details')
async def consent_details(payload: ConsentRequest, user: AuthenticatedUser = Depends(get_current_user)):
    async with admin_db_session(reason='verified_oauth_consent_details') as db:
        row = await pending_request(db, payload.request, user.id)
        client = await oauth_provider.get_client(row.client_id)
        if not client:
            raise HTTPException(400, 'Client is unavailable.')
        await db.commit()
        return JSONResponse({'client_name': client.client_name or 'MCP client', 'client_id': row.client_id,
            'redirect_uri': row.payload['redirect_uri'], 'scopes': row.payload['scopes'],
            'resource': resource(), 'expires_at': utc(row.expires_at).isoformat()}, headers=PRIVATE)


@router.post('/oauth/consent/decision')
async def consent_decision(payload: ConsentDecision, user: AuthenticatedUser = Depends(get_current_user)):
    async with admin_db_session(reason='verified_oauth_consent_decision') as db:
        row = await pending_request(db, payload.request, user.id)
        scopes = sorted(set(payload.scopes))
        if set(scopes) - set(row.payload['scopes']) or set(scopes) - set(SCOPES):
            raise HTTPException(400, 'Consent cannot add unrequested scopes.')
        if payload.approve and not set(scopes).difference({'offline_access'}):
            raise HTTPException(400, 'Select at least one permission, or deny this request.')
        row.consumed_at = now()
        params = {'state': row.payload.get('state'), 'iss': issuer()}
        if payload.approve:
            client = await oauth_provider.get_client(row.client_id)
            if not client:
                raise HTTPException(400, 'Client is unavailable.')
            grant = OAuthGrant(user_id=user.id, client_id=row.client_id, client_name=client.client_name or 'MCP client',
                scopes=scopes, issuer=issuer(), resource=resource(), expires_at=now() + timedelta(days=REFRESH_DAYS))
            db.add(grant)
            await db.flush()
            code = secrets.token_urlsafe(32)
            db.add(OAuthCode(code_hash=digest(code), user_id=user.id, grant_id=grant.id,
                code_challenge=row.payload['code_challenge'], redirect_uri=row.payload['redirect_uri'],
                expires_at=now() + timedelta(minutes=2)))
            params['code'] = code
            db.add(AuditLog(user_id=user.id, event_type='mcp_oauth_connected', target_entity='oauth_grant',
                target_id=grant.id, details={'scope_count': len(scopes)}))
        else:
            params['error'] = 'access_denied'
        redirect = construct_redirect_uri(row.payload['redirect_uri'], **{k: v for k, v in params.items() if v is not None})
        await db.commit()
        return JSONResponse({'redirect_to': redirect}, headers=PRIVATE)


@router.get('/api/v1/mcp/oauth/connections')
async def connections(user: AuthenticatedUser = Depends(get_current_user), db=Depends(get_rls_db_session)):
    rows = (await db.execute(select(OAuthGrant).where(OAuthGrant.user_id == user.id)
        .order_by(OAuthGrant.created_at.desc()).limit(100))).scalars().all()
    return [{key: getattr(row, key) for key in ('id', 'client_name', 'scopes', 'created_at', 'last_used_at', 'expires_at', 'revoked_at')} for row in rows]


@router.delete('/api/v1/mcp/oauth/connections/{grant_id}')
async def disconnect(grant_id: UUID, user: AuthenticatedUser = Depends(get_current_user)):
    async with admin_db_session(reason='verified_oauth_disconnect') as db:
        row = (await db.execute(select(OAuthGrant).where(OAuthGrant.user_id == user.id, OAuthGrant.id == str(grant_id))
            .with_for_update())).scalar_one_or_none()
        if not row:
            raise HTTPException(404, 'Connection not found.')
        if not row.revoked_at:
            row.revoked_at = now()
            db.add(AuditLog(user_id=user.id, event_type='mcp_oauth_revoked', target_entity='oauth_grant', target_id=row.id, details={}))
            await db.commit()
        return {'revoked': True}
