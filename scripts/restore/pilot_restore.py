"""Restore the private staging archive only into a newly initialized loopback PG17 cluster."""
import argparse
import asyncio
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backup'))
from encrypt_backup import decrypt
from staging_recovery import (
    SCHEMAS,
    manifest,
    private_directory,
    private_setup,
    quote,
    unpack_private,
)


def run(command, env=None, timeout=180):
    # A Windows postmaster can inherit pg_ctl's captured pipe handles and keep
    # subprocess.communicate waiting after pg_ctl has exited. Daemons use NUL.
    control = Path(command[0]).name.lower() in ('pg_ctl', 'pg_ctl.exe')
    return subprocess.run([str(item) for item in command], env=env,
        stdout=subprocess.DEVNULL if control else subprocess.PIPE,
        stderr=subprocess.DEVNULL if control else subprocess.PIPE,
        check=True, timeout=timeout).stdout or b''


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    if port < 1024:
        raise RuntimeError('Unsafe restore port.')
    return port


async def bootstrap(conn, original):
    # Recreate owners/privileges without copying source passwords or permitting login.
    for role in original['roles']:
        flags = ['SUPERUSER' if role['rolsuper'] else 'NOSUPERUSER',
            'INHERIT' if role['rolinherit'] else 'NOINHERIT',
            'CREATEROLE' if role['rolcreaterole'] else 'NOCREATEROLE',
            'CREATEDB' if role['rolcreatedb'] else 'NOCREATEDB',
            'REPLICATION' if role['rolreplication'] else 'NOREPLICATION',
            'BYPASSRLS' if role['rolbypassrls'] else 'NOBYPASSRLS']
        await conn.execute(f'CREATE ROLE {quote(role["rolname"])} NOLOGIN ' + ' '.join(flags))
    for membership in original['memberships']:
        if membership['role'] == 'sb_recovery_operator' or membership['member'] == 'sb_recovery_operator':
            raise RuntimeError('Unexpected role collision.')
        options = ', '.join(f'{name} {str(membership[key]).upper()}' for name, key in (
            ('ADMIN', 'admin_option'), ('INHERIT', 'inherit_option'), ('SET', 'set_option')))
        await conn.execute(f'GRANT {quote(membership["role"])} TO {quote(membership["member"])} WITH {options}')
    await conn.execute('CREATE SCHEMA IF NOT EXISTS extensions')
    for schema in original['schemas']:
        name, owner = quote(schema['nspname']), quote(schema['owner'])
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {name} AUTHORIZATION {owner}')
        await conn.execute(f'ALTER SCHEMA {name} OWNER TO {owner}')
    for extension in original['extensions']:
        name = extension['extname']
        if name in ('plpgsql', 'supabase_vault'):
            continue
        owner = extension['owner']
        source_role = next(row for row in original['roles'] if row['rolname'] == owner)
        await conn.execute('ALTER ROLE ' + quote(owner) + ' SUPERUSER')
        try:
            await conn.execute('SET ROLE ' + quote(owner))
            version = extension['extversion'].replace("'", "''")
            await conn.execute(f'CREATE EXTENSION {quote(name)} WITH SCHEMA {quote(extension["nspname"])} VERSION \'{version}\'')
        finally:
            await conn.execute('RESET ROLE')
            if not source_role['rolsuper']:
                await conn.execute('ALTER ROLE ' + quote(owner) + ' NOSUPERUSER')


def comparison(original, restored):
    def acl(value):
        # pg_restore may emit equivalent ACL items in another order.
        if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
            return ','.join(sorted(value[1:-1].split(',')))
        return value

    def canonical(value):
        if isinstance(value, dict):
            return {key: acl(item) if key in ('acl', 'defaclacl') else canonical(item)
                for key, item in value.items()}
        if isinstance(value, list):
            return [canonical(item) for item in value]
        return value

    sections = ['tables', 'columns', 'policies', 'functions', 'constraints', 'indexes', 'triggers', 'schemas', 'default_acl']
    results = {section: canonical(original[section]) == canonical(restored[section]) for section in sections}
    if 'roles' in original:
        def role_permissions(rows):
            return [{key: value for key, value in row.items() if key != 'rolcanlogin'}
                for row in rows if row['rolname'] != 'sb_recovery_operator']

        results['role_permissions'] = role_permissions(original['roles']) == role_permissions(restored['roles'])
        results['role_memberships'] = original['memberships'] == restored['memberships']
        results['source_role_logins_disabled'] = all(not row['rolcanlogin']
            for row in restored['roles'] if row['rolname'] != 'sb_recovery_operator')
    if 'extensions' in original:
        def extensions(rows):
            return [{key: value for key, value in row.items() if key != 'owner' or row['extname'] != 'plpgsql'}
                for row in rows if row['extname'] != 'supabase_vault']

        results['extension_versions'] = extensions(original['extensions']) == extensions(restored['extensions'])
    return results


def restore_list(contents):
    """Select application objects plus schema/default ACLs, without managed extensions.

    pg_restore --schema omits the schema objects themselves and their ACLs.
    Schemas are created from the private manifest before applying this list.
    """
    schemas = '|'.join(re.escape(name) for name in SCHEMAS)
    selected = []
    for line in contents.splitlines():
        entry = re.sub(r'^\d+; \d+ \d+ ', '', line)
        namespaced = re.match(rf'^[A-Z ]+ ({schemas}) ', entry)
        schema_metadata = re.match(rf'^(ACL|COMMENT|SECURITY LABEL) - SCHEMA ({schemas}) ', entry)
        global_defaults = entry.startswith('DEFAULT ACL - ')
        if namespaced or schema_metadata or global_defaults:
            selected.append(line)
    if not selected:
        raise ValueError('No application objects in the backup.')
    return '\n'.join(selected) + '\n'


async def restore(encrypted, config_path, work_dir, server_root, client_root):
    config = private_setup(config_path)
    work_dir = await asyncio.to_thread(private_directory, work_dir)
    scratch = Path(tempfile.mkdtemp(prefix='isolated_restore_', dir=work_dir)).resolve()
    if not scratch.is_relative_to(work_dir) or not scratch.name.startswith('isolated_restore_'):
        raise RuntimeError('Unsafe restore workspace.')
    server_root, client_root = Path(server_root).resolve(), Path(client_root).resolve()
    version = (await asyncio.to_thread(run, [server_root / 'bin/postgres.exe', '--version'])).decode()
    if 'PostgreSQL) 17.' not in version:
        raise RuntimeError('Restore requires PostgreSQL 17.')
    port, password = free_port(), secrets.token_urlsafe(32)
    password_file, data = scratch / 'local-secret', scratch / 'data'
    password_file.write_text(password, encoding='ascii')
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
    env.update(PGHOST='127.0.0.1', PGPORT=str(port), PGDATABASE='postgres',
        PGUSER='sb_recovery_operator', PGPASSWORD=password, PGSSLMODE='disable', PGCONNECT_TIMEOUT='10')
    try:
        unpack_private(decrypt(Path(encrypted).read_bytes(), config['passphrase']), scratch)
        original = json.loads((scratch / 'manifest.json').read_text())
        await asyncio.to_thread(run, [server_root / 'bin/initdb.exe', '-D', data,
            '-U', 'sb_recovery_operator', '-A', 'scram-sha-256', '--pwfile', password_file,
            '--encoding=UTF8', '--locale=C'])
        password_file.unlink()
        await asyncio.to_thread(run, [server_root / 'bin/pg_ctl.exe', '-D', data,
            '-l', scratch / 'server-private.log', '-o', f'-h 127.0.0.1 -p {port} -c timezone=UTC', '-w', 'start'])
        conn = await asyncpg.connect(host='127.0.0.1', port=port, user='sb_recovery_operator',
            password=password, database='postgres', ssl=False, server_settings={'timezone': 'UTC'})
        try:
            # Fresh initdb has no application/Auth/Storage tables. Never connect to a remote target.
            if await conn.fetchval("SELECT count(*) FROM pg_tables WHERE schemaname IN ('public','auth','storage')"):
                raise RuntimeError('Restore target is not empty.')
            await bootstrap(conn, original)
        finally:
            await conn.close()
        toc = await asyncio.to_thread(run, [client_root / 'pg_restore.exe', '--list', scratch / 'database.dump'])
        selection = scratch / 'restore.list'
        selection.write_text(restore_list(toc.decode('utf-8')), encoding='utf-8')
        command = [client_root / 'pg_restore.exe', '--exit-on-error', '--single-transaction', '--no-tablespaces',
            '--dbname', 'postgres', '--use-list', selection, scratch / 'database.dump']
        await asyncio.to_thread(run, command, env, 600)
        conn = await asyncpg.connect(host='127.0.0.1', port=port, user='sb_recovery_operator',
            password=password, database='postgres', ssl=False, server_settings={'timezone': 'UTC'})
        try:
            restored = await manifest(conn)
            results = comparison(original, restored)
            vector = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname='vector'")
        finally:
            await conn.close()
        report = {'database_restore': 'PASS' if all(results.values()) else 'FAIL', 'checks': results,
            'source_project': original.get('source_project', 'unknown'),
            'scope': SCHEMAS, 'table_count': len(restored['tables']), 'postgres': restored['version'],
            'vector': vector, 'encrypted_sha256': hashlib.sha256(Path(encrypted).read_bytes()).hexdigest(),
            'auth_service_config': 'SEPARATE_GATE', 'storage_file_bytes': 'SEPARATE_GATE',
            'vault_extension': 'Managed Supabase extension excluded from local application-scope restore',
            'role_logins': 'Disabled on restored source roles; passwords not copied',
            'plaintext_cleanup': 'PENDING'}
        if not all(results.values()):
            # Definitions and digests remain private; only boolean results go to the report/log.
            (work_dir / 'comparison-private.json').write_text(json.dumps({'source': original, 'restored': restored}, default=str))
        report_path = work_dir / 'restore-report.json'
        report_path.write_text(json.dumps(report, indent=2))
    finally:
        # A startup command can time out after the postmaster has already started.
        # Never delete its files until this exact newly initialized cluster stops.
        if (data / 'postmaster.pid').exists():
            await asyncio.to_thread(run, [server_root / 'bin/pg_ctl.exe', '-D', data, '-m', 'fast', '-w', 'stop'])
        # Only this newly created cluster and plaintext extraction, never an existing/live target.
        if scratch.is_relative_to(work_dir) and scratch.name.startswith('isolated_restore_'):
            await asyncio.to_thread(shutil.rmtree, scratch)
    report['plaintext_cleanup'] = 'Temporary plaintext files and restored cluster removed; SSD erasure cannot be guaranteed'
    report_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('encrypted', 'private-setup', 'work-dir', 'server-root', 'client-root'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    try:
        result = asyncio.run(restore(args.encrypted, args.private_setup, args.work_dir, args.server_root, args.client_root))
        raise SystemExit(0 if result['database_restore'] == 'PASS' else 1)
    except Exception as error:  # noqa: BLE001 -- never emit private SQL/server errors or source row values
        print(json.dumps({'database_restore': 'BLOCKED', 'error_type': type(error).__name__}))
        raise SystemExit(1) from None
