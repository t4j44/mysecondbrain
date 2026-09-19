"""Real dump/restore proof on a disposable loopback PostgreSQL server only.

The CI server already has the migrated schema and Supabase role shims. This
checks PostgreSQL recovery, not hosted Supabase or Storage object recovery.
"""
import asyncio
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'apps' / 'api'))


def load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def verify():
    import asyncpg
    from app.db.dsn import to_libpq_dsn
    from app.db.rls import identity_statements

    raw = os.environ.get('POSTGRES_TEST_DATABASE_URL', '')
    parsed = urlsplit(to_libpq_dsn(raw))
    if os.environ.get('RUN_ISOLATED_RESTORE_PROOF') != '1' or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        raise SystemExit('Restore proof requires explicit opt-in and a disposable loopback test database.')
    if 'test' not in parsed.path.lower():
        raise SystemExit('Source database name must explicitly identify a test database.')
    target = 'brain_restore_test_' + uuid4().hex
    target_url = urlunsplit(parsed._replace(path='/' + target))
    owners = [uuid4(), uuid4()]
    record_id = uuid4()
    source = await asyncpg.connect(to_libpq_dsn(raw))
    created = False
    try:
        async with source.transaction():
            for owner in owners:
                await source.execute('INSERT INTO auth.users(id,email) VALUES($1,$2)', owner, str(owner) + '@restore.test')
            await source.execute('INSERT INTO public.memories(id,user_id,title,body) VALUES($1,$2,$3,$4)',
                                 record_id, owners[0], 'Recovery fixture', 'Synthetic cobalt evidence')
        # target is a fixed prefix plus generated hex; never user-controlled SQL.
        await source.execute('CREATE DATABASE "' + target + '"')
        created = True
        os.environ['DATABASE_URL'] = to_libpq_dsn(raw)
        os.environ['BACKUP_DIR'] = str(ROOT / '.test-tmp' / 'restore-proof')
        backup = load_script('restore_proof_backup', 'scripts/backup/backup.py')
        dump = await asyncio.to_thread(backup.run_backup)
        os.environ['RESTORE_ALLOW_ISOLATED'] = '1'
        os.environ['RESTORE_DATABASE_URL'] = target_url
        restore = load_script('restore_proof_restore', 'scripts/restore/restore.py')
        await asyncio.to_thread(restore.restore_backup, dump)
        restored = await asyncpg.connect(target_url)
        try:
            assert await restored.fetchval('SELECT body FROM public.memories WHERE id=$1', record_id) == 'Synthetic cobalt evidence'
            for owner, expected in [(owners[0], 1), (owners[1], 0)]:
                async with restored.transaction():
                    # The same claims and role used by the app; SQL placeholders adapted for asyncpg.
                    for statement, params in identity_statements(str(owner)):
                        key, value = next(iter(params.items()))
                        await restored.execute(statement.replace(':' + key, '$1'), value)
                    assert await restored.fetchval('SELECT count(*) FROM public.memories WHERE id=$1', record_id) == expected
        finally:
            await restored.close()
        env = {**os.environ, 'POSTGRES_TEST_DATABASE_URL': target_url}
        await asyncio.to_thread(subprocess.run, [sys.executable, '-m', 'pytest', 'apps/api/tests/integration',
            '-q', '-o', 'addopts=', '--junitxml=restore-results.xml'], cwd=ROOT, env=env, check=True)
        await asyncio.to_thread(subprocess.run, [sys.executable, 'scripts/check_test_evidence.py', 'restore-results.xml'],
                                cwd=ROOT, env=env, check=True)
        print('PASS: real PostgreSQL dump, isolated restore, exact fixture content, owner/foreign RLS and restored integration suite.')
    finally:
        try:
            if created:
                await source.execute('DROP DATABASE "' + target + '"')
            for owner in owners:
                await source.execute('DELETE FROM auth.users WHERE id=$1', owner)
        finally:
            await source.close()


if __name__ == '__main__':
    try:
        asyncio.run(verify())
    except Exception:  # noqa: BLE001 - CLI failure boundary must not print connection secrets
        raise SystemExit('Restore proof FAILED. No recovery certification was recorded.') from None
