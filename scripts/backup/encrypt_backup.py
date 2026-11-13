"""Authenticated SBBK1 backup envelope, compatible with the existing local helper."""
import argparse
import getpass
import hashlib
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b'SBBK1'
MAX_BYTES = 512 * 1024 * 1024


def key(passphrase, salt):
    if len(passphrase) < 20:
        raise ValueError('Use a passphrase of at least 20 characters.')
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(passphrase.encode())


def encrypt(data, passphrase):
    if len(data) > MAX_BYTES:
        raise ValueError('Backup exceeds the pilot encryption memory limit.')
    salt, nonce = os.urandom(16), os.urandom(12)
    return MAGIC + salt + nonce + AESGCM(key(passphrase, salt)).encrypt(nonce, data, MAGIC)


def decrypt(data, passphrase):
    if not 49 <= len(data) <= MAX_BYTES + 49 or data[:5] != MAGIC:
        raise ValueError('Invalid encrypted backup envelope.')
    return AESGCM(key(passphrase, data[5:21])).decrypt(data[21:33], data[33:], MAGIC)


def read_bounded(source, maximum=None):
    maximum = MAX_BYTES + 49 if maximum is None else maximum
    source = Path(source)
    if source.stat().st_size > maximum:
        raise ValueError('Backup exceeds the pilot encryption memory limit.')
    with source.open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('Backup exceeds the pilot encryption memory limit.')
    return data


def transform(mode, src, dst, passphrase):
    src, dst = Path(src), Path(dst)
    data = (encrypt if mode == 'enc' else decrypt)(read_bounded(src), passphrase)
    # Authenticate fully before creating plaintext. Never overwrite an existing backup.
    with dst.open('xb') as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    return hashlib.sha256(data).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['enc', 'dec'])
    parser.add_argument('source')
    parser.add_argument('destination')
    args = parser.parse_args()
    try:
        digest = transform(args.mode, args.source, args.destination,
            os.environ.get('BACKUP_PASSPHRASE') or getpass.getpass('Backup passphrase: '))
        print(f'Authenticated backup operation completed. SHA256: {digest}')
    except Exception:  # noqa: BLE001 -- sanitized CLI boundary, never expose credentials in tracebacks
        raise SystemExit('Backup encryption/decryption failed; no successful recovery recorded.') from None
