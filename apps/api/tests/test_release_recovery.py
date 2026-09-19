"""Failure-path tests for the release scripts; not a real restore certificate."""
import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[3]


def load_script(relative):
    spec = importlib.util.spec_from_file_location('release_script', ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_bootstrap_refuses_nonempty_schema_before_mutation(monkeypatch):
    import asyncpg
    bootstrap = load_script('scripts/db/bootstrap_migrations.py')
    connection = SimpleNamespace(fetchval=AsyncMock(return_value=1), execute=AsyncMock(), close=AsyncMock())
    monkeypatch.setattr(asyncpg, 'connect', AsyncMock(return_value=connection))
    with pytest.raises(SystemExit, match='empty public schema'):
        await bootstrap.apply_migrations('postgresql://local:synthetic@localhost/test')
    connection.execute.assert_not_awaited()
    connection.close.assert_awaited_once()


def test_bootstrap_never_echoes_password_and_requires_remote_opt_in(monkeypatch):
    bootstrap = load_script('scripts/db/bootstrap_migrations.py')
    monkeypatch.delenv('BOOTSTRAP_ALLOW_ISOLATED', raising=False)
    monkeypatch.setenv('POSTGRES_TEST_DATABASE_URL', 'postgresql://tester:private_fixture@db.production.example/test')
    with pytest.raises(SystemExit) as error:
        bootstrap.resolve_target_url()
    assert 'private_fixture' not in str(error.value)
    monkeypatch.setenv('POSTGRES_TEST_DATABASE_URL', 'postgresql://tester:private_fixture@db.staging.example/test')
    with pytest.raises(SystemExit, match='BOOTSTRAP_ALLOW_ISOLATED'):
        bootstrap.resolve_target_url()
    monkeypatch.setenv('BOOTSTRAP_ALLOW_ISOLATED', '1')
    assert bootstrap.resolve_target_url().endswith('/test')


def test_backup_failure_does_not_leave_a_successful_archive(monkeypatch, tmp_path):
    backup = load_script('scripts/backup/backup.py')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://tester:synthetic@localhost/test')
    monkeypatch.setenv('BACKUP_DIR', str(tmp_path))
    def fail(command, **kwargs):
        Path(command[-1]).write_bytes(b'partial')
        raise subprocess.CalledProcessError(1, command)
    monkeypatch.setattr(subprocess, 'run', fail)
    with pytest.raises(SystemExit, match='Backup failed'):
        backup.run_backup()
    assert list(tmp_path.iterdir()) == []


def test_backup_preserves_grants_and_validates_dump(monkeypatch, tmp_path):
    backup = load_script('scripts/backup/backup.py')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://tester:synthetic@localhost/test?sslmode=require')
    monkeypatch.setenv('BACKUP_DIR', str(tmp_path))
    monkeypatch.setenv('PGHOSTADDR', '198.51.100.1')
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert '--no-acl' not in command
        if command[0] == 'pg_dump':
            assert kwargs['env']['PGSSLMODE'] == 'require'
            assert 'PGHOSTADDR' not in kwargs['env']
            Path(command[-1]).write_bytes(b'synthetic dump' * 100)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, 'run', run)
    archive = backup.run_backup()
    assert archive.suffix == '.dump' and archive.exists()
    assert calls[1][0:2] == ['pg_restore', '--list']


def test_restore_refuses_nonempty_target(monkeypatch, tmp_path):
    restore = load_script('scripts/restore/restore.py')
    dump = tmp_path / 'fixture.dump'
    dump.write_bytes(b'synthetic')
    monkeypatch.setenv('RESTORE_ALLOW_ISOLATED', '1')
    monkeypatch.setenv('RESTORE_DATABASE_URL', 'postgresql://tester:synthetic@localhost/test_restore')
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=b'3', returncode=0)
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(SystemExit, match='restore failed'):
        restore.restore_backup(dump)
    assert len(calls) == 1 and calls[0][0] == 'psql'


@pytest.mark.parametrize('status', [302, 429, 500, 503])
def test_storage_verification_never_counts_outage_as_isolation(status):
    verifier = load_script('scripts/verify_storage_isolation.py')
    with pytest.raises(AssertionError, match='explicit access denial'):
        verifier.expect_denied(SimpleNamespace(status_code=status))


def test_storage_verification_accepts_explicit_denial():
    verifier = load_script('scripts/verify_storage_isolation.py')
    verifier.expect_denied(SimpleNamespace(status_code=403))
