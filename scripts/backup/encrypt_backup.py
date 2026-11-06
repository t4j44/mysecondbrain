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


def transform(mode, src, dst, passphrase):
    src, dst = Path(src), Path(dst)
    if src.stat().st_size > MAX_BYTES + 49:
        raise ValueError('Backup exceeds the pilot encryption memory limit.')
    data = (encrypt if mode == 'enc' else decrypt)(src.read_bytes(), passphrase)
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
    except Exception:
        raise SystemExit('Backup encryption/decryption failed; no successful recovery recorded.') from None
