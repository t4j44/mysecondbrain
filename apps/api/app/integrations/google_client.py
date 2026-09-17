"""Google OAuth and user-approved exports/actions; Supabase is authoritative."""
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

import httpx
from sqlalchemy import select, text

from app.core.config import settings
from app.core.errors import IntegrationError
from app.core.security import decrypt_token, encrypt_token
from app.dependencies.database import admin_db_session
from app.models.entities import Integration, JobRecord, Task
from app.repositories.integrations import IntegrationRepository

SCOPES = {'google_drive': 'https://www.googleapis.com/auth/drive.file',
          'google_calendar': 'https://www.googleapis.com/auth/calendar.events'}

class GoogleIntegrationService:
    def __init__(self, db, user_id):
        self.db, self.user_id = db, str(user_id)
        self.repo = IntegrationRepository()

    def require_config(self):
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise IntegrationError('Google connection needs server configuration.', code='GOOGLE_NOT_CONFIGURED', status_code=503)

    async def authorize(self, provider: str):
        self.require_config()
        if provider not in SCOPES:
            raise IntegrationError('Unsupported Google integration.')
        state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
        self.db.add(JobRecord(user_id=self.user_id, job_type='google_oauth_state', status='pending',
            result_payload={'state_hash': hashlib.sha256(state.encode()).hexdigest(),
                'verifier': encrypt_token(verifier), 'provider': provider}))
        await self.db.commit()
        return {'url': 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
            'client_id': settings.GOOGLE_CLIENT_ID, 'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'response_type': 'code', 'scope': SCOPES[provider], 'access_type': 'offline',
            'prompt': 'consent', 'state': state, 'code_challenge': challenge, 'code_challenge_method': 'S256'})}

    async def connect_oauth_callback(self, code: str, state: str | None):
        self.require_config()
        if not state:
            raise IntegrationError('Missing authorization state.', status_code=400)
        digest = hashlib.sha256(state.encode()).hexdigest()
        rows = (await self.db.execute(select(JobRecord).where(JobRecord.user_id == self.user_id,
            JobRecord.job_type == 'google_oauth_state', JobRecord.status == 'pending',
            JobRecord.created_at > datetime.now(timezone.utc) - timedelta(minutes=10)
        ).with_for_update())).scalars().all()
        state_job = next((row for row in rows if secrets.compare_digest(row.result_payload.get('state_hash', ''), digest)), None)
        if state_job is None:
            raise IntegrationError('Authorization expired or already used. Connect again.', status_code=400)
        provider = state_job.result_payload['provider']
        verifier = decrypt_token(state_job.result_payload['verifier'])
        # Consume before exchange. A failed exchange requires a new authorization.
        state_job.status, state_job.result_payload = 'completed', {'provider': provider}
        await self.db.commit()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post('https://oauth2.googleapis.com/token', data={
                'code': code, 'client_id': settings.GOOGLE_CLIENT_ID, 'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI, 'grant_type': 'authorization_code', 'code_verifier': verifier})
        if response.status_code != 200:
            raise IntegrationError('Google authorization failed. Connect again.', status_code=400)
        tokens = response.json()
        granted = tokens.get('scope', '').split()
        if SCOPES[provider] not in granted or not tokens.get('access_token'):
            raise IntegrationError('The requested Google permission was not granted.', status_code=403)
        integration = await self.repo.get_by_provider(self.db, self.user_id, provider)
        if integration is None:
            integration = Integration(user_id=self.user_id, provider_name=provider, status='disconnected')
            self.db.add(integration)
            await self.db.flush()
        integration.scopes = granted
        await self.db.commit()
        await self._store_tokens(str(integration.id), tokens)
        integration.is_connected = True
        await self.db.commit()
        return {'status': 'connected', 'provider': provider, 'scopes_granted': granted,
                'message': 'Google connection verified.'}

    async def _store_tokens(self, integration_id: str, tokens: dict):
        async with admin_db_session(reason='google_token_vault_write') as vault:
            await vault.execute(text('''INSERT INTO integration_tokens
                (user_id, integration_id, encrypted_access_token, encrypted_refresh_token, expires_at)
                SELECT CAST(:owner AS uuid), id, :access, :refresh, :expiry FROM integrations
                WHERE id=CAST(:integration AS uuid) AND user_id=CAST(:owner AS uuid)
                ON CONFLICT (integration_id) DO UPDATE SET encrypted_access_token=EXCLUDED.encrypted_access_token,
                encrypted_refresh_token=COALESCE(EXCLUDED.encrypted_refresh_token, integration_tokens.encrypted_refresh_token),
                expires_at=EXCLUDED.expires_at, updated_at=NOW()'''),
                {'owner': self.user_id, 'integration': integration_id, 'access': encrypt_token(tokens['access_token']),
                 'refresh': encrypt_token(tokens['refresh_token']) if tokens.get('refresh_token') else None,
                 'expiry': datetime.now(timezone.utc) + timedelta(seconds=int(tokens.get('expires_in', 3600)))})
            await vault.commit()

    async def access_token(self, provider: str):
        integration = await self.repo.get_by_provider(self.db, self.user_id, provider)
        if not integration or not integration.is_connected or SCOPES[provider] not in integration.scopes:
            raise IntegrationError('Connect Google and grant the required permission first.', status_code=409)
        async with admin_db_session(reason='google_token_vault_read') as vault:
            row = (await vault.execute(text('''SELECT encrypted_access_token, encrypted_refresh_token, expires_at
                FROM integration_tokens WHERE integration_id=CAST(:id AS uuid) AND user_id=CAST(:owner AS uuid)'''),
                {'id': str(integration.id), 'owner': self.user_id})).mappings().first()
        if not row:
            raise IntegrationError('Google credentials are unavailable. Reconnect.', status_code=409)
        if row['expires_at'] and row['expires_at'] > datetime.now(timezone.utc) + timedelta(seconds=60):
            return decrypt_token(row['encrypted_access_token'])
        if not row['encrypted_refresh_token']:
            raise IntegrationError('Google authorization expired. Reconnect.', status_code=409)
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post('https://oauth2.googleapis.com/token', data={
                'client_id': settings.GOOGLE_CLIENT_ID, 'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'grant_type': 'refresh_token', 'refresh_token': decrypt_token(row['encrypted_refresh_token'])})
        if response.status_code != 200:
            raise IntegrationError('Google authorization expired or was revoked. Reconnect.', status_code=409)
        tokens = response.json()
        await self._store_tokens(str(integration.id), tokens)
        return tokens['access_token']

    async def disconnect_provider(self, provider_name):
        integration = await self.repo.get_by_provider(self.db, self.user_id, provider_name)
        if not integration:
            return False
        async with admin_db_session(reason='google_token_vault_revoke') as vault:
            await vault.execute(text('DELETE FROM integration_tokens WHERE integration_id=CAST(:id AS uuid) AND user_id=CAST(:owner AS uuid)'),
                {'id': str(integration.id), 'owner': self.user_id})
            await vault.commit()
        integration.is_connected = False
        await self.db.commit()
        return True

    async def _enqueue(self, provider, payload):
        await self.access_token(provider)
        job = JobRecord(user_id=self.user_id, job_type='sync_' + provider, status='pending', result_payload=payload)
        self.db.add(job)
        await self.db.flush()
        return job

    async def trigger_drive_sync_job(self, folder_id=None, sync_mode='one_way'):
        if sync_mode != 'one_way':
            raise IntegrationError('This beta supports export to Drive only.')
        return await self._enqueue('google_drive', {'folder_id': folder_id})

    async def trigger_calendar_sync_job(self, calendar_id='primary'):
        return await self._enqueue('google_calendar', {'calendar_id': calendar_id})

    async def export_drive(self, payload):
        token = await self.access_token('google_drive')
        # Only user-owned, active records; no remote AI involved in archival.
        from app.ai.indexing import SOURCES, record_text
        lines = ['# Second Brain private archive', '', 'Supabase is the source of truth.', '']
        for kind, (model, _fields) in SOURCES.items():
            query = select(model).where(model.user_id == self.user_id, model.deleted_at.is_(None))
            if hasattr(model, 'archived_at'):
                query = query.where(model.archived_at.is_(None))
            rows = (await self.db.execute(query)).scalars().all()
            lines.append('## ' + kind)
            for row in rows:
                lines.extend([record_text(row, kind), ''])
        headers = {'Authorization': 'Bearer ' + token}
        # Serialize archive identity allocation across concurrent jobs for this account.
        await self.db.execute(select(Integration).where(Integration.user_id == self.user_id,
            Integration.provider_name == 'google_drive').with_for_update())
        # One persisted per-owner archive identity; updates do not create duplicates.
        identity = (await self.db.execute(select(JobRecord).where(JobRecord.user_id == self.user_id,
            JobRecord.job_type == 'drive_archive_identity').with_for_update())).scalars().first()
        async with httpx.AsyncClient(timeout=30) as client:
            if identity is None:
                generated = await client.get('https://www.googleapis.com/drive/v3/files/generateIds', headers=headers, params={'count': 1, 'space': 'drive'})
                generated.raise_for_status()
                identity = JobRecord(user_id=self.user_id, job_type='drive_archive_identity', status='completed', result_payload={'file_id': generated.json()['ids'][0]})
                self.db.add(identity)
                await self.db.commit()
            file_id = identity.result_payload['file_id']
            existing = await client.get('https://www.googleapis.com/drive/v3/files/' + quote(file_id, safe=''), headers=headers)
            if existing.status_code == 404:
                meta = {'id': file_id, 'name': 'Second Brain.md', 'mimeType': 'text/markdown'}
                if payload.get('folder_id'):
                    meta['parents'] = [payload['folder_id']]
                created = await client.post('https://www.googleapis.com/drive/v3/files', headers=headers, json=meta)
                if created.status_code != 409:
                    created.raise_for_status()
            else:
                existing.raise_for_status()
            updated = await client.patch('https://www.googleapis.com/upload/drive/v3/files/' + quote(file_id, safe=''),
                headers={**headers, 'Content-Type': 'text/markdown; charset=utf-8'}, params={'uploadType': 'media'}, content='\n\n'.join(lines).encode())
            updated.raise_for_status()
        return {'file_id': file_id, 'status': 'exported'}

    async def sync_calendar(self, payload):
        token = await self.access_token('google_calendar')
        calendar = quote(payload.get('calendar_id', 'primary'), safe='')
        base = f'https://www.googleapis.com/calendar/v3/calendars/{calendar}/events'
        tasks = (await self.db.execute(select(Task).where(Task.user_id == self.user_id,
            Task.deleted_at.is_(None), Task.archived_at.is_(None)))).scalars().all()
        count = 0
        async with httpx.AsyncClient(timeout=30) as client:
            for task in tasks:
                metadata = task.calendar_sync_metadata or {}
                if not metadata.get('enabled') or (payload.get('task_id') and str(task.id) != payload['task_id']):
                    continue
                event_id = task.gcal_event_id or hashlib.sha256(f'{self.user_id}:{task.id}:{metadata.get("generation", 0)}'.encode()).hexdigest()[:32]
                headers = {'Authorization': 'Bearer ' + token}
                if metadata.get('cancel'):
                    response = await client.delete(base + '/' + event_id, headers=headers, params={'sendUpdates': 'none'})
                    if response.status_code not in (200, 204, 404, 410):
                        response.raise_for_status()
                    task.calendar_sync_metadata = {**metadata, 'enabled': False, 'status': 'cancelled',
                        'generation': metadata.get('generation', 0) + 1}
                    task.gcal_event_id = None
                else:
                    event = {'summary': task.title, 'start': {'dateTime': metadata['start'], 'timeZone': metadata['timezone']},
                             'end': {'dateTime': metadata['end'], 'timeZone': metadata['timezone']}}
                    response = await client.post(base, headers=headers, params={'sendUpdates': 'none'}, json={'id': event_id, **event})
                    if response.status_code == 409:
                        response = await client.patch(base + '/' + event_id, headers=headers, params={'sendUpdates': 'none'}, json=event)
                    response.raise_for_status()
                    task.gcal_event_id = event_id
                    task.calendar_sync_metadata = {**metadata, 'status': 'synced', 'calendar_id': payload.get('calendar_id', 'primary')}
                count += 1
                await self.db.commit()
        return {'events_synced': count}
