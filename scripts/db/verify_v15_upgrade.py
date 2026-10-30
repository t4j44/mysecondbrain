"""Upgrade a seeded V1 schema on a generated, disposable loopback database only."""
import asyncio
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from bootstrap_migrations import AUTH_SHIM_SQL, POST_MIGRATION_GRANT_SQL, migration_paths, validate

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'apps' / 'api'))


async def verify():
    import asyncpg
    from app.db.dsn import to_libpq_dsn
    raw = os.environ.get('POSTGRES_TEST_DATABASE_URL', '')
    parsed = urlsplit(to_libpq_dsn(raw))
    if os.environ.get('RUN_ISOLATED_UPGRADE_PROOF') != '1' or parsed.hostname not in {'localhost', '127.0.0.1', '::1'} or 'test' not in parsed.path.lower():
        raise SystemExit('Upgrade proof requires explicit opt-in and a disposable loopback test server.')
    name = 'brain_upgrade_test_' + uuid4().hex
    target_url = urlunsplit(parsed._replace(path='/' + name))
    control = await asyncpg.connect(to_libpq_dsn(raw))
    created = False
    try:
        await control.execute('CREATE DATABASE "' + name + '"')
        created = True
        conn = await asyncpg.connect(target_url)
        try:
            await conn.execute(AUTH_SHIM_SQL)
            paths = migration_paths()
            split = next(i for i, path in enumerate(paths) if path.name == '20260927000029_context_events.sql')
            for path in paths[:split]:
                await conn.execute(path.read_text(encoding='utf-8'))
            owner, person, project, edge = [uuid4() for _ in range(4)]
            await conn.execute('INSERT INTO auth.users(id,email) VALUES($1,$2)', owner, str(owner) + '@upgrade.test')
            await conn.execute("INSERT INTO public.people(id,user_id,name) VALUES($1,$2,'Synthetic V1 contact')", person, owner)
            await conn.execute("INSERT INTO public.projects(id,user_id,name) VALUES($1,$2,'Synthetic V1 project')", project, owner)
            await conn.execute("INSERT INTO public.entity_edges(id,user_id,source_entity_type,source_entity_id,target_entity_type,target_entity_id,relationship_type) VALUES($1,$2,'person',$3,'project',$4,'related_to')", edge, owner, person, project)
            old_time = await conn.fetchval('SELECT created_at FROM public.entity_edges WHERE id=$1', edge)
            for path in paths[split:]:
                async with conn.transaction():
                    await conn.execute(path.read_text(encoding='utf-8'))
            await conn.execute(POST_MIGRATION_GRANT_SQL)
            retained = await conn.fetchrow('SELECT recorded_at,valid_to,source_event_id FROM public.entity_edges WHERE id=$1', edge)
            assert retained['recorded_at'] == old_time and retained['valid_to'] is None and retained['source_event_id'] is None
            assert await conn.fetchval('SELECT name FROM public.people WHERE id=$1', person) == 'Synthetic V1 contact'
            # The old edge can become historical and a new current edge can coexist.
            await conn.execute('UPDATE public.entity_edges SET valid_to=now() WHERE id=$1', edge)
            await conn.execute("INSERT INTO public.entity_edges(user_id,source_entity_type,source_entity_id,target_entity_type,target_entity_id,relationship_type) VALUES($1,'person',$2,'project',$3,'related_to')", owner, person, project)
            assert await conn.fetchval('SELECT count(*) FROM public.entity_edges WHERE user_id=$1', owner) == 2
            await conn.execute('DELETE FROM auth.users WHERE id=$1', owner)
        finally:
            await conn.close()
        await validate(target_url)
        env = {**os.environ, 'POSTGRES_TEST_DATABASE_URL': target_url}
        await asyncio.to_thread(subprocess.run, [sys.executable, '-m', 'pytest', 'apps/api/tests/integration',
            '-q', '-o', 'addopts=', '--junitxml=upgrade-results.xml'], cwd=ROOT, env=env, check=True)
        await asyncio.to_thread(subprocess.run, [sys.executable, 'scripts/check_test_evidence.py', 'upgrade-results.xml'],
                                cwd=ROOT, env=env, check=True)
        print('PASS: seeded V1 upgrade, retained temporal history and upgraded PostgreSQL integration suite.')
    finally:
        if created:
            await control.execute('DROP DATABASE "' + name + '"')
        await control.close()


if __name__ == '__main__':
    try:
        asyncio.run(verify())
    except Exception:
        raise SystemExit('V1.5 upgrade proof FAILED. No upgrade certification was recorded.') from None
