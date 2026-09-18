"""Durable account closure and secret-free portable canonical data exports."""
import csv
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from sqlalchemy import MetaData, delete, select, text, update

from app.core.config import settings
from app.core.errors import AppError, ConflictError
from app.dependencies.database import admin_db_session
from app.integrations.storage_client import StorageService
from app.models.base import Base
from app.models.entities import AccountClosure, Profile
from app.models.publication import PortfolioPublication

EXCLUDED = {"account_closures", "integration_tokens", "jobs", "sync_jobs", "export_jobs", "export_items",
            "exports", "embedding_jobs", "embeddings", "memory_embeddings"}


async def schema_tables(db):
    if db.bind.dialect.name == 'postgresql':
        metadata = MetaData()
        conn = await db.connection()
        await conn.run_sync(lambda sync: metadata.reflect(bind=sync, schema='public'))
        return metadata.sorted_tables
    return Base.metadata.sorted_tables


def public_value(value):
    if isinstance(value, dict):
        return {k: public_value(v) for k, v in value.items() if k not in {
            'mcp_credentials', 'token_hash', 'key_hash', 'salt', 'encrypted_access_token',
            'encrypted_refresh_token', 'access_token', 'refresh_token'}}
    if isinstance(value, list):
        return [public_value(v) for v in value]
    return value


async def portable_export(db, owner):
    result = {}
    for table in await schema_tables(db):
        if table.name in EXCLUDED:
            continue
        column = table.c.get('user_id') if table.name != 'profiles' else table.c.get('id')
        if column is None:
            continue
        rows = (await db.execute(select(table).where(column == owner).limit(100001))).mappings().all()
        if len(rows) > 100000:
            raise AppError('Export exceeds the beta limit; contact support for a complete export.', status_code=413)
        result[table.name] = [public_value(dict(row)) for row in rows]
    encoded = json.dumps({'format_version': 1, 'tables': result}, default=str, ensure_ascii=False).encode()
    if len(encoded) > 100 * 1024**2:
        raise AppError('Export exceeds the beta limit; contact support.', status_code=413)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('data.json', encoded)
        summary = ['# Second Brain account export', '', 'Original attachment bytes are not included. Documents metadata retains their identifiers.', '']
        for name, rows in result.items():
            summary += [f'## {name}', f'{len(rows)} records', '']
            if not rows:
                continue
            output = io.StringIO(newline='')
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                safe = {}
                for key, value in row.items():
                    value = json.dumps(value, default=str, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value) if value is not None else ''
                    # CSV formula injection protection; JSON retains exact originals.
                    safe[key] = "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value
                writer.writerow(safe)
            archive.writestr(f'csv/{name}.csv', output.getvalue())
            archive.writestr(f'markdown/{name}.md', '# ' + name + '\n\n' + '\n\n'.join(
                '\n'.join(f'- {key}: {value}' for key, value in row.items()) for row in rows))
        archive.writestr('README.md', '\n'.join(summary))
    return buffer.getvalue()


async def request_closure(owner):
    owner = str(UUID(owner))
    async with admin_db_session(reason='verified_account_closure') as db:
        if db.bind.dialect.name == 'postgresql':
            await db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:owner, 17))'), {'owner': owner})
        receipt = await db.get(AccountClosure, owner)
        if receipt:
            return receipt.status
        receipt = AccountClosure(user_id=owner, status='pending')
        db.add(receipt)
        # Public reads use a narrow admin path: revoke snapshots immediately.
        await db.execute(update(PortfolioPublication).where(PortfolioPublication.user_id == owner)
                         .values(revoked_at=datetime.now(timezone.utc)))
        profile = await db.get(Profile, owner)
        if profile:
            profile.settings = {**(profile.settings or {}), 'mcp_credentials': []}
        await db.commit()
    return 'pending'


async def delete_auth_user(owner):
    if not settings.SUPABASE_URL or not settings.supabase_secret:
        raise AppError('Supabase account deletion needs server configuration.', code='AUTH_DELETE_UNCONFIGURED')
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.delete(settings.SUPABASE_URL.rstrip('/') + '/auth/v1/admin/users/' + str(UUID(owner)),
            headers={'apikey': settings.supabase_secret, 'Authorization': 'Bearer ' + settings.supabase_secret})
        if response.status_code not in (200, 204, 404):
            raise AppError('Supabase account deletion failed; cleanup will retry.', code='AUTH_DELETE_FAILED')


async def close_account(owner):
    # Block all owner transactions before touching external storage. Retry-safe steps.
    async with admin_db_session(reason='account_closure_claim') as db:
        receipt = await db.get(AccountClosure, owner)
        if not receipt or receipt.status == 'completed':
            return
    await StorageService().delete_owner_files(owner)
    async with admin_db_session(reason='account_erasure') as db:
        for table in reversed(await schema_tables(db)):
            if table.name == 'account_closures':
                continue
            column = table.c.get('user_id') if table.name != 'profiles' else table.c.get('id')
            if column is not None:
                await db.execute(delete(table).where(column == owner))
        await db.commit()
    await delete_auth_user(owner)
    async with admin_db_session(reason='account_closure_receipt') as db:
        receipt = await db.get(AccountClosure, owner)
        receipt.status, receipt.error_code = 'completed', None
        receipt.updated_at = datetime.now(timezone.utc)
        await db.commit()


async def process_closures():
    async with admin_db_session(reason='account_closure_poll') as db:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        receipts = (await db.execute(select(AccountClosure).where(
            (AccountClosure.status == 'pending') | ((AccountClosure.status.in_(['processing', 'failed'])) &
            (AccountClosure.updated_at < cutoff))).limit(5).with_for_update(skip_locked=True))).scalars().all()
        owners = [str(row.user_id) for row in receipts]
        for row in receipts:
            row.status, row.updated_at = 'processing', datetime.now(timezone.utc)
        await db.commit()
    for owner in owners:
        try:
            await close_account(owner)
        except Exception:
            async with admin_db_session(reason='account_closure_failure') as db:
                receipt = await db.get(AccountClosure, owner)
                if receipt:
                    receipt.status, receipt.error_code = 'failed', 'CLEANUP_RETRY_REQUIRED'
                    receipt.updated_at = datetime.now(timezone.utc)
                    await db.commit()


async def require_active(db, owner):
    if await db.get(AccountClosure, owner):
        raise ConflictError('Account deletion is in progress. Only deletion status remains available.')
