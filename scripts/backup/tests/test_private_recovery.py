import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from cryptography.exceptions import InvalidTag

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'restore'))
from encrypt_backup import decrypt, encrypt, transform
from pilot_restore import comparison
from staging_recovery import archive_bytes, staging_url, unpack_private

PHRASE = 'Synthetic recovery phrase for tests only'


class PrivateRecoveryTests(unittest.TestCase):
    def test_authenticated_roundtrip_and_fresh_nonce(self):
        payload = b'Only synthetic fixture bytes'
        first, second = encrypt(payload, PHRASE), encrypt(payload, PHRASE)
        self.assertNotEqual(first, second)
        self.assertEqual(decrypt(first, PHRASE), payload)

    def test_wrong_phrase_and_tampering_fail(self):
        original = encrypt(b'Synthetic fixture', PHRASE)
        with self.assertRaises(InvalidTag):
            decrypt(original, PHRASE + 'wrong')
        for position in (5, 21, 34, len(original) - 1):
            altered = bytearray(original)
            altered[position] ^= 1
            with self.assertRaises(InvalidTag):
                decrypt(bytes(altered), PHRASE)

    def test_bad_envelope_and_short_phrase_fail(self):
        for value in (b'', b'SBBK1', b'unknown' * 10):
            with self.assertRaises(ValueError):
                decrypt(value, PHRASE)
        with self.assertRaises(ValueError):
            encrypt(b'a', 'short')

    def test_unauthenticated_plaintext_is_never_written(self):
        with tempfile.TemporaryDirectory() as root:
            source, target = Path(root) / 'source', Path(root) / 'plain'
            source.write_bytes(encrypt(b'Synthetic fixture', PHRASE))
            with self.assertRaises(InvalidTag):
                transform('dec', source, target, PHRASE + 'wrong')
            self.assertFalse(target.exists())

    def test_existing_destination_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as root:
            source, target = Path(root) / 'source', Path(root) / 'existing'
            source.write_bytes(b'synthetic')
            target.write_bytes(b'preserved')
            with self.assertRaises(FileExistsError):
                transform('enc', source, target, PHRASE)
            self.assertEqual(target.read_bytes(), b'preserved')

    def test_staging_only_connection_guard(self):
        allowed = 'postgresql://postgres.rpkjmdrralzxhdsgceal:synthetic@aws-0-test.pooler.supabase.com:5432/postgres'
        self.assertEqual(staging_url(allowed), allowed)
        for bad in (allowed.replace('rpkjmdrralzxhdsgceal', 'production'),
                allowed.replace(':5432/', ':6543/'), allowed.replace('/postgres', '/other'),
                allowed.replace('pooler.supabase.com', 'pooler.supabase.com.attacker.test'),
                'postgresql://postgres:synthetic@127.0.0.1:5432/postgres'):
            with self.assertRaises(ValueError):
                staging_url(bad)

    def test_archive_roundtrip_has_only_dump_and_private_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root)
            dump = folder / 'input.dump'
            dump.write_bytes(b'Synthetic PostgreSQL custom dump')
            out = folder / 'restore'
            out.mkdir()
            unpack_private(decrypt(encrypt(archive_bytes(dump, {'tables': []}), PHRASE), PHRASE), out)
            self.assertEqual((out / 'database.dump').read_bytes(), dump.read_bytes())
            self.assertEqual(sorted(p.name for p in out.iterdir()), ['database.dump', 'manifest.json'])

    def test_traversal_extra_members_and_links_rejected(self):
        for member_name, kind in (('../escape', tarfile.REGTYPE), ('database.dump', tarfile.SYMTYPE)):
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                entry = tarfile.TarInfo(member_name)
                entry.type, entry.linkname = kind, 'elsewhere'
                archive.addfile(entry)
                archive.addfile(tarfile.TarInfo('manifest.json'))
            with tempfile.TemporaryDirectory() as root, self.assertRaises(ValueError):
                unpack_private(stream.getvalue(), root)

    def test_comparison_detects_record_and_security_drift(self):
        sections = ('tables', 'columns', 'policies', 'functions', 'constraints', 'indexes', 'triggers', 'schemas', 'default_acl')
        original = {name: [{'digest': 'synthetic', 'acl': '{a,b}'}] for name in sections}
        equivalent = {name: [{'digest': 'synthetic', 'acl': '{b,a}'}] for name in sections}
        self.assertTrue(all(comparison(original, equivalent).values()))
        for section in sections:
            changed = {**equivalent, section: [{'digest': 'changed', 'acl': '{b,a}'}]}
            self.assertFalse(comparison(original, changed)[section])


if __name__ == '__main__':
    unittest.main()
