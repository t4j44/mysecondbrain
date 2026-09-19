"""Checked PostgreSQL custom-format dump. Storage bytes require separate backup."""
import datetime
import os
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from uuid import uuid4


def pg_environment(url):
    parsed = urlsplit(url.replace('postgresql+asyncpg://', 'postgresql://'))
    if parsed.scheme not in {'postgres', 'postgresql'} or not parsed.hostname:
        raise ValueError('A PostgreSQL URL is required')
    # Inherited PG service/host settings must never override the explicit target.
    environment = {**{k: v for k, v in os.environ.items() if not k.startswith('PG')},
            'PGHOST': parsed.hostname, 'PGPORT': str(parsed.port or 5432),
            'PGDATABASE': unquote(parsed.path.lstrip('/')), 'PGUSER': unquote(parsed.username or ''),
            'PGPASSWORD': unquote(parsed.password or '')}
    options = parse_qs(parsed.query)
    for query, variable in {'sslmode': 'PGSSLMODE', 'sslrootcert': 'PGSSLROOTCERT',
                            'connect_timeout': 'PGCONNECT_TIMEOUT'}.items():
        if query in options:
            environment[variable] = options[query][-1]
    return environment


def run_backup():
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise SystemExit('DATABASE_URL is required; do not paste it into logs.')
    folder = Path(os.environ.get('BACKUP_DIR', './backups')).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S') + '_' + uuid4().hex[:8]
    partial = folder / f'brain_{stamp}.partial'
    final = folder / f'brain_{stamp}.dump'
    try:
        subprocess.run(['pg_dump', '--format=custom', '--no-owner', '--file', str(partial)],
            env=pg_environment(url), check=True, timeout=600, stderr=subprocess.DEVNULL)
        if not partial.exists() or partial.stat().st_size < 100:
            raise RuntimeError('Empty database dump')
        subprocess.run(['pg_restore', '--list', str(partial)], check=True, timeout=60,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        partial.replace(final)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
        partial.unlink(missing_ok=True)
        raise SystemExit('Backup failed; no successful backup was recorded.') from None
    print(f'Database dump verified: {final.name}. Storage object bytes are NOT included.')
    return final


if __name__ == '__main__':
    run_backup()
