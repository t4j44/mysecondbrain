"""Verify a saved private setup without printing its URL, password or passphrase."""
import argparse
import hashlib
import json
from pathlib import Path

from staging_recovery import private_setup, staging_url


def verify(path, *, allow_synthetic=False):
    path = Path(path).resolve(strict=True)
    expected = Path.home() / 'secure' / 'SecondBrainRecovery'
    if path.parent != expected.resolve():
        raise ValueError('Private setup must stay in the private folder outside Git/worktrees.')
    config = private_setup(path, allow_synthetic=allow_synthetic)
    staging_url(config['database_url'])
    if len(config['passphrase']) < 20:
        raise ValueError('Backup passphrase is too short.')
    return {'file_exists': True, 'windows_decryption': 'PASS', 'staging_target': 'PASS',
        'outside_git_worktrees': True, 'bytes': path.stat().st_size,
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'synthetic_test': bool(config.get('synthetic_test'))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', required=True)
    parser.add_argument('--allow-synthetic', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.path, allow_synthetic=args.allow_synthetic)))
    except Exception as error:  # noqa: BLE001 -- do not expose credentials through exception text
        print(json.dumps({'verification': 'FAIL', 'error_type': type(error).__name__}))
        raise SystemExit(1) from None
