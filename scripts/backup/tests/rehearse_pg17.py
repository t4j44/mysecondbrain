"""Actual local synthetic PG17 rehearsal; never evidence of hosted staging recovery."""
import argparse
import asyncio
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'restore'))
import pilot_restore
from backup import run_backup
from encrypt_backup import encrypt
from staging_recovery import archive_bytes, manifest

PHRASE = 'Synthetic local rehearsal phrase only'


async def rehearse(server_root, client_root, workspace):
    root, clients = Path(server_root).resolve(), Path(client_root).resolve()
    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix='synthetic_source_', dir=workspace))
    data, secret = scratch / 'data', scratch / 'password'
    password, port = secrets.token_urlsafe(32), pilot_restore.free_port()
    secret.write_text(password, encoding='ascii')
    started = False
    env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
    env.update(PGHOST='127.0.0.1', PGPORT=str(port), PGDATABASE='postgres', PGUSER='postgres',
        PGPASSWORD=password, PGSSLMODE='disable')
    try:
        await asyncio.to_thread(pilot_restore.run, [root / 'bin/initdb.exe', '-D', data, '-U', 'postgres',
            '-A', 'scram-sha-256', '--pwfile', secret, '--encoding=UTF8', '--locale=C'])
        secret.unlink()
        await asyncio.to_thread(pilot_restore.run, [root / 'bin/pg_ctl.exe', '-D', data,
            '-l', scratch / 'server.log', '-o', f'-h 127.0.0.1 -p {port} -c timezone=UTC', '-w', 'start'])
        started = True
        conn = await asyncpg.connect(host='127.0.0.1', port=port, user='postgres', password=password,
            database='postgres', ssl=False, server_settings={'timezone': 'UTC'})
        try:
            await conn.execute('''CREATE ROLE anon NOLOGIN; CREATE ROLE authenticated NOLOGIN;
                CREATE ROLE service_role NOLOGIN BYPASSRLS;
                GRANT anon TO authenticated WITH ADMIN FALSE, INHERIT FALSE, SET TRUE;
                CREATE SCHEMA auth; CREATE SCHEMA storage; CREATE SCHEMA extensions;
                CREATE EXTENSION vector WITH SCHEMA extensions VERSION '0.8.2';
                CREATE TABLE auth.users(id uuid PRIMARY KEY,email text);
                CREATE TABLE storage.buckets(id text PRIMARY KEY,public boolean NOT NULL);
                CREATE TABLE storage.objects(id uuid PRIMARY KEY,bucket_id text REFERENCES storage.buckets(id),name text);
                CREATE TABLE public.memories(id uuid PRIMARY KEY,user_id uuid REFERENCES auth.users(id),
                    body text,embedding extensions.vector(3));
                CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS
                    $$ SELECT nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
                ALTER TABLE public.memories ENABLE ROW LEVEL SECURITY;
                CREATE POLICY owner_only ON public.memories TO authenticated USING(user_id=auth.uid()) WITH CHECK(user_id=auth.uid());
                GRANT USAGE ON SCHEMA public,auth TO authenticated;
                GRANT SELECT,INSERT,UPDATE,DELETE ON public.memories TO authenticated;
                INSERT INTO auth.users VALUES('00000000-0000-4000-a000-000000000001','synthetic-a@example.invalid'),
                    ('00000000-0000-4000-a000-000000000002','synthetic-b@example.invalid');
                INSERT INTO public.memories VALUES('00000000-0000-4000-a000-000000000003',
                    '00000000-0000-4000-a000-000000000001','Synthetic recovery fixture','[1,2,3]');
                INSERT INTO storage.buckets VALUES('synthetic-private',false);''')
            metadata = await manifest(conn)
            metadata['source_project'] = 'synthetic-local-pg17'
            url = f'postgresql://postgres:{password}@127.0.0.1:{port}/postgres'
            os.environ['PATH'] = str(clients) + os.pathsep + os.environ.get('PATH', '')
            dump = await asyncio.to_thread(run_backup, connection_url=url, backup_dir=scratch,
                connection_environment=env, preserve_owners=True)
            encrypted = workspace / ('synthetic_' + secrets.token_hex(8) + '.enc')
            encrypted.write_bytes(encrypt(archive_bytes(dump, metadata), PHRASE))
            dump.unlink()
        finally:
            await conn.close()
        with patch.object(pilot_restore, 'private_setup', return_value={'passphrase': PHRASE}):
            report = await pilot_restore.restore(encrypted, 'synthetic-not-owner-credentials', workspace, root, clients)
        if report['database_restore'] != 'PASS':
            raise RuntimeError('Synthetic restore comparison failed.')
        print(json.dumps({'synthetic_rehearsal': 'PASS', 'hosted_staging_recovery': 'NOT_RUN'}))
    finally:
        if started:
            await asyncio.to_thread(pilot_restore.run, [root / 'bin/pg_ctl.exe', '-D', data, '-m', 'fast', '-w', 'stop'])
        if scratch.resolve().is_relative_to(workspace) and scratch.name.startswith('synthetic_source_'):
            await asyncio.to_thread(shutil.rmtree, scratch)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('server-root', 'client-root', 'workspace'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    try:
        asyncio.run(rehearse(args.server_root, args.client_root, args.workspace))
    except Exception as error:  # noqa: BLE001 -- sanitized boundary
        print(json.dumps({'synthetic_rehearsal': 'FAIL', 'error_type': type(error).__name__}))
        if isinstance(error, subprocess.CalledProcessError):
            # This entry point constructs only its own synthetic source; never use
            # verbose subprocess errors in the actual private staging restore CLI.
            print('SYNTHETIC REHEARSAL ONLY: ' + Path(error.cmd[0]).name)
            print((error.stderr or b'').decode(errors='replace')[:2000])
        raise SystemExit(1) from None
