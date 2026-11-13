"""Read-only staging export and private authenticated archive. Never logs record values."""
import argparse
import asyncio
import ctypes
import hashlib
import io
import json
import os
import shutil
import ssl
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import asyncpg
import certifi
from backup import pg_environment, run_backup
from encrypt_backup import MAX_BYTES, decrypt, encrypt

PROJECT = 'rpkjmdrralzxhdsgceal'
SCHEMAS = ['public', 'auth', 'storage', 'supabase_migrations']
MAX_MANIFEST_BYTES = 8 * 1024 * 1024
# Reserve bounded tar/gzip overhead below the encryption envelope limit.
MAX_DUMP_BYTES = MAX_BYTES - MAX_MANIFEST_BYTES - 1024 * 1024


def staging_url(value):
    parsed = urlsplit(value)
    direct = parsed.hostname == f'db.{PROJECT}.supabase.co'
    pooler = (bool(parsed.hostname) and parsed.hostname.endswith('.pooler.supabase.com')
        and (parsed.username or '').endswith('.' + PROJECT))
    if (parsed.scheme not in ('postgres', 'postgresql') or not (direct or pooler)
            or parsed.path != '/postgres' or parsed.port not in (None, 5432) or not parsed.password
            or parsed.fragment or set(parse_qs(parsed.query, keep_blank_values=True)) - {'sslmode', 'connect_timeout'}):
        raise ValueError('Only the specified staging session/direct connection is accepted.')
    return value


def private_setup(path, *, allow_synthetic=False):
    if os.name != 'nt':
        raise RuntimeError('Private setup requires Windows DPAPI.')
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]

    raw = Path(path).read_bytes()
    buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    source, target = Blob(len(raw), buffer), Blob()
    crypt = ctypes.windll.crypt32.CryptUnprotectData
    crypt.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.restype = wintypes.BOOL
    if not crypt(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)):
        raise RuntimeError('Private setup could not be unlocked by this Windows account.')
    try:
        config = json.loads(ctypes.string_at(target.data, target.length))
        if config.get('synthetic_test') and not allow_synthetic:
            raise ValueError('Synthetic private setup cannot be used for a real backup.')
        return config
    finally:
        ctypes.memset(target.data, 0, target.length)
        ctypes.windll.kernel32.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))


def quote(name):
    return '"' + name.replace('"', '""') + '"'


def private_directory(folder):
    folder = Path(folder).absolute()
    if os.name == 'nt':
        subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-File',
            str(Path(__file__).with_name('private_directory.ps1')), '-Path', str(folder)],
            check=True, capture_output=True, timeout=30)
    else:
        if folder.is_symlink():
            raise ValueError('Recovery work directory cannot be a symbolic link.')
        folder.mkdir(parents=True, exist_ok=True)
        folder.chmod(0o700)
    return folder


async def manifest(conn):
    """Compare full definitions, ACLs, row counts and content digests without printing data."""
    tables = await conn.fetch('''SELECT n.nspname AS schema, c.relname AS name,
        pg_get_userbyid(c.relowner) AS owner, c.relrowsecurity AS rls, c.relforcerowsecurity AS force_rls,
        coalesce(c.relacl::text,'') AS acl FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname=ANY($1::text[]) AND c.relkind IN ('r','p') ORDER BY 1,2''', SCHEMAS)
    result = {'version': await conn.fetchval("SELECT current_setting('server_version')"), 'tables': []}
    for table in tables:
        name = quote(table['schema']) + '.' + quote(table['name'])
        data = await conn.fetchrow(f'''SELECT count(*) AS count,
            md5(coalesce(string_agg(d, '' ORDER BY d),'')) AS digest
            FROM (SELECT md5(to_jsonb(t)::text) AS d FROM {name} t) record_digests''')
        result['tables'].append({**dict(table), **dict(data)})
    queries = {
        'columns': '''SELECT table_schema,table_name,column_name,ordinal_position,data_type,udt_schema,udt_name,
            is_nullable,column_default,is_identity,identity_generation FROM information_schema.columns
            WHERE table_schema=ANY($1::text[]) ORDER BY table_schema,table_name,ordinal_position''',
        'policies': '''SELECT schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check
            FROM pg_policies WHERE schemaname=ANY($1::text[]) ORDER BY 1,2,3''',
        'functions': '''SELECT n.nspname AS schema,p.proname,pg_get_function_identity_arguments(p.oid) AS arguments,
            pg_get_functiondef(p.oid) AS definition,pg_get_userbyid(p.proowner) AS owner,
            coalesce(p.proacl::text,'') AS acl FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname=ANY($1::text[]) AND p.prokind IN ('f','p') ORDER BY 1,2,3''',
        'constraints': '''SELECT n.nspname AS schema,c.relname,con.conname,pg_get_constraintdef(con.oid) AS definition
            FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname=ANY($1::text[]) ORDER BY 1,2,3''',
        'indexes': '''SELECT schemaname,tablename,indexname,indexdef FROM pg_indexes
            WHERE schemaname=ANY($1::text[]) ORDER BY 1,2,3''',
        'triggers': '''SELECT n.nspname AS schema,c.relname,t.tgname,pg_get_triggerdef(t.oid) AS definition
            FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname=ANY($1::text[]) AND NOT t.tgisinternal ORDER BY 1,2,3''',
        'schemas': '''SELECT nspname,pg_get_userbyid(nspowner) AS owner,coalesce(nspacl::text,'') AS acl
            FROM pg_namespace WHERE nspname=ANY($1::text[]) ORDER BY 1''',
        'default_acl': '''SELECT pg_get_userbyid(d.defaclrole) AS owner,n.nspname,d.defaclobjtype,d.defaclacl::text
            FROM pg_default_acl d LEFT JOIN pg_namespace n ON n.oid=d.defaclnamespace
            WHERE n.nspname=ANY($1::text[]) OR d.defaclnamespace=0 ORDER BY 1,2,3''',
    }
    for key, query in queries.items():
        result[key] = [dict(row) for row in await conn.fetch(query, SCHEMAS)]
    result['extensions'] = [dict(row) for row in await conn.fetch('''SELECT e.extname,e.extversion,n.nspname,
        pg_get_userbyid(e.extowner) AS owner FROM pg_extension e JOIN pg_namespace n ON n.oid=e.extnamespace ORDER BY 1''')]
    result['roles'] = [dict(row) for row in await conn.fetch('''SELECT rolname,rolsuper,rolinherit,rolcreaterole,
        rolcreatedb,rolcanlogin,rolreplication,rolbypassrls FROM pg_roles WHERE rolname NOT LIKE 'pg_%' ORDER BY 1''')]
    result['memberships'] = [dict(row) for row in await conn.fetch('''SELECT pg_get_userbyid(roleid) AS role,
        pg_get_userbyid(member) AS member,admin_option,inherit_option,set_option FROM pg_auth_members
        ORDER BY 1,2''')]
    return result


def archive_bytes(dump, metadata):
    dump = Path(dump)
    size = dump.stat().st_size
    if size > MAX_DUMP_BYTES:
        raise ValueError('Database dump exceeds the pilot recovery limit.')
    # Encode incrementally so metadata cannot allocate an unbounded serialized copy.
    manifest_data = io.BytesIO()
    for part in json.JSONEncoder(sort_keys=True, default=str).iterencode(metadata):
        encoded = part.encode()
        if manifest_data.tell() + len(encoded) > MAX_MANIFEST_BYTES:
            raise ValueError('Manifest exceeds the pilot recovery limit.')
        manifest_data.write(encoded)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        info = tarfile.TarInfo('database.dump')
        info.size, info.mode = size, 0o600
        with dump.open('rb') as source:
            archive.addfile(info, source)
        info = tarfile.TarInfo('manifest.json')
        info.size, info.mode = manifest_data.tell(), 0o600
        manifest_data.seek(0)
        archive.addfile(info, manifest_data)
    if output.tell() > MAX_BYTES:
        raise ValueError('Recovery archive exceeds the encryption limit.')
    return output.getvalue()


def unpack_private(data, folder):
    """No tar extraction API: only our two regular members, no links/traversal."""
    folder = Path(folder)
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        members = archive.getmembers()
        if sorted(item.name for item in members) != ['database.dump', 'manifest.json']:
            raise ValueError('Unexpected recovery archive members.')
        limits = {'database.dump': MAX_DUMP_BYTES, 'manifest.json': MAX_MANIFEST_BYTES}
        for member in members:
            if not member.isfile() or not 0 <= member.size <= limits[member.name]:
                raise ValueError('Invalid recovery archive member.')
        for member in members:
            with (folder / member.name).open('xb') as target:
                shutil.copyfileobj(archive.extractfile(member), target, length=1024 * 1024)


async def close_and_remove_dump(conn, dump):
    """Cleanup still runs if a connection raises or never finishes closing."""
    try:
        await asyncio.wait_for(conn.close(), timeout=10)
    finally:
        if dump:
            # Do not swallow an unlink failure: the CLI must remain BLOCKED.
            Path(dump).unlink(missing_ok=True)


async def run_private_dump(**options):
    """A cancelled coroutine must still collect and remove its thread's plaintext.

    pg_dump itself has a bounded subprocess timeout. Keep its snapshot alive until
    it ends, even after cooperative cancellation. Forced process termination or
    power loss cannot provide a cleanup guarantee.
    """
    worker = asyncio.create_task(asyncio.to_thread(run_backup, **options))
    cancelled = False
    while True:
        try:
            dump = await asyncio.shield(worker)
            break
        except asyncio.CancelledError:
            cancelled = True
            if worker.cancelled():
                raise
    if cancelled:
        Path(dump).unlink(missing_ok=True)
        raise asyncio.CancelledError
    return dump


async def export(config_path, folder):
    config = private_setup(config_path)
    url = staging_url(config['database_url'])
    folder = await asyncio.to_thread(private_directory, folder)
    environment = pg_environment(url)
    environment.update(PGSSLMODE='verify-full', PGSSLROOTCERT=certifi.where(), PGCONNECT_TIMEOUT='15',
        PGOPTIONS='-c default_transaction_read_only=on -c statement_timeout=120000 -c lock_timeout=10000')
    context = ssl.create_default_context(cafile=certifi.where())
    conn = await asyncpg.connect(url, ssl=context, timeout=15,
        server_settings={'default_transaction_read_only': 'on', 'statement_timeout': '120000', 'timezone': 'UTC'})
    dump = None
    try:
        async with conn.transaction(isolation='repeatable_read', readonly=True):
            snapshot = await conn.fetchval('SELECT pg_export_snapshot()')
            metadata = await manifest(conn)
            metadata['source_project'] = PROJECT
            metadata['snapshot_at'] = datetime.now(timezone.utc).isoformat()
            dump = await run_private_dump(preserve_owners=True, snapshot=snapshot,
                connection_url=url, backup_dir=folder, connection_environment=environment)
            plaintext = archive_bytes(dump, metadata)
        encrypted = encrypt(plaintext, config['passphrase'])
        if decrypt(encrypted, config['passphrase']) != plaintext:
            raise RuntimeError('Authenticated round trip mismatch.')
        target = folder / (dump.stem + '.tar.gz.enc')
        with target.open('xb') as output:
            output.write(encrypted)
            output.flush()
            os.fsync(output.fileno())
        print(json.dumps({'status': 'EXPORTED_ENCRYPTED_NOT_RESTORED', 'file': str(target),
            'bytes': len(encrypted), 'sha256': hashlib.sha256(encrypted).hexdigest(),
            'table_count': len(metadata['tables']), 'storage_bytes_included': False}))
        return target
    finally:
        await close_and_remove_dump(conn, dump)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-setup', required=True)
    parser.add_argument('--work-dir', required=True)
    args = parser.parse_args()
    try:
        asyncio.run(export(args.private_setup, args.work_dir))
    except Exception as error:  # noqa: BLE001 -- private CLI boundary must not print server errors/credentials
        print(json.dumps({'status': 'BLOCKED', 'error_type': type(error).__name__,
            'detail': 'Private export did not complete. No recovery PASS recorded.'}))
        raise SystemExit(1) from None
