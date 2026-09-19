"""Restore only to an explicitly designated empty isolated PostgreSQL database."""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('brain_backup', Path(__file__).resolve().parents[1] / 'backup' / 'backup.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def restore_backup(backup_file_path):
    if os.environ.get('RESTORE_ALLOW_ISOLATED') != '1' or not os.environ.get('RESTORE_DATABASE_URL'):
        raise SystemExit('Set RESTORE_ALLOW_ISOLATED=1 and RESTORE_DATABASE_URL to an EMPTY isolated target.')
    path = Path(backup_file_path).resolve(strict=True)
    env = module.pg_environment(os.environ['RESTORE_DATABASE_URL'])
    try:
        probe = subprocess.run(['psql', '-X', '-At', '-v', 'ON_ERROR_STOP=1', '-c',
            "SELECT count(*) FROM pg_tables WHERE schemaname='public'"], env=env, check=True,
            capture_output=True, timeout=30)
        if probe.stdout.strip() != b'0':
            raise RuntimeError('Restore target is not empty')
        # Preserve grants: a restored database without authenticated-role privileges is not usable.
        # The isolated target server must already contain the roles referenced by the dump.
        subprocess.run(['pg_restore', '--exit-on-error', '--single-transaction', '--no-owner',
            '--dbname', env['PGDATABASE'], str(path)], env=env, check=True, timeout=600, stderr=subprocess.DEVNULL)
        print('Dump restored into isolated target. Run schema/RLS/content and Storage verification before trusting recovery.')
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        raise SystemExit('Isolated restore failed. No successful restore was recorded.') from None


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: restore.py <database.dump>')
    restore_backup(sys.argv[1])
